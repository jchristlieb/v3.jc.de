from fabric import api as fab
from functools import wraps
import os, re

#########################################################################################################
# Init / Settings

# Set the working directory to the build/ directory. This is necessary if you
# run "fab ..." in a subdirectory or with "fab ... -f build/fabfile.py"
BUILD_PATH = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
os.chdir(BUILD_PATH)


#########################################################################################################
# Utils

def _web_path():
  return os.path.realpath(os.path.join(BUILD_PATH, '..', 'web'))


def _goto_web(func):
  @wraps(func)
  def goto_func(*args, **kwargs):
    with fab.lcd(_web_path()):
      return func(*args, **kwargs)

  return goto_func


def _create_path(path):
  if not os.path.exists(path):
    os.makedirs(path)


def _scss_paths():
  for dir, dirnames, filenames in os.walk(os.path.join(_web_path(), 'app', 'themes')):
    for dirname in dirnames:
      if dirname in ('scss', 'sass',):
        scss_path = os.path.join(dir, dirname)
        yield scss_path


def _filtered_files(paths, pattern):
  if not isinstance(paths, (list, tuple)):
    paths = [paths]
  for path in paths:
    for dir, dirnames, filenames in os.walk(path):
      for filename in filenames:
        filepath = os.path.join(dir, filename)
        if pattern.match(filepath):
          yield filepath


def _execute_watch(paths, func, **event_handler_kwargs):
  from watchdog.observers import Observer
  from watchdog.events import RegexMatchingEventHandler
  import time

  class FuncEventHandler(RegexMatchingEventHandler):
    def on_any_event(self, event):
      func(event)

  if not isinstance(paths, (list, tuple)):
    paths = [paths]
  event_handler = FuncEventHandler(**event_handler_kwargs)
  observer = Observer()
  for path in paths:
    for i in path:
      observer.schedule(event_handler, i, recursive=True)
  observer.start()
  try:
    while True:
      time.sleep(1)
  except KeyboardInterrupt:
    observer.stop()
  observer.join()


#########################################################################################################
# Tasks


@fab.task
@_goto_web
def css():
  for filepath in _filtered_files(list(_scss_paths()), re.compile('.*/[^_/][^/]*\.scss$')):
    output_filepath = filepath.replace('scss', 'css').replace('sass', 'css')
    _create_path(os.path.dirname(output_filepath))
    fab.local('sassc -lm %s %s' % (filepath, output_filepath))


@fab.task
@_goto_web
def watch():
  def handle_event(event):
    with fab.settings(warn_only=True):
      fab.execute(css)

  fab.execute(css)
  _execute_watch(
    _scss_paths(),
    handle_event,
    regexes=['^.*\.(scss)$'],
    ignore_directories=True,
  )


# Setup / Install

# Deployment

def _deploy_git_factory():
  import fabdeploit

  class GitFilter(fabdeploit.GitFilter):
    def filter(self):

      #fab.execute(css)
      for filename in (
        'nova',
        'vendor',
      ):
        if os.path.exists(os.path.join(self.repo.working_tree_dir, filename)):
          self.add(filename)
        else:
          raise RuntimeError('File %s does not exist?' % filename)

  class Git(fabdeploit.Git):
    local_repository_path = os.path.dirname(BUILD_PATH)
    release_author = 'Jan Christlieb <mail@janchristlieb.de>'
    release_commit_filter_class = GitFilter

  return Git


def _deploy_base_env():
  fab.require('git')

  fab.env.use_ssh_config = True


@fab.task
def production():
  fab.env.git = _deploy_git_factory()(
    remote_repository_path='',  # get this ready
    release_branch='production',
  )

  _deploy_base_env()
  fab.env.hosts = ['jan.mittwald']

@fab.task
def staging():
  fab.env.git = _deploy_git_factory()(
    remote_repository_path='/home/www/p461591/html/staging.janchristlieb.de',  # get this ready
    release_branch='staging',
  )

  _deploy_base_env()
  fab.env.hosts = ['jan.mittwald']

@fab.task
def deploy_push_files():
  fab.require('git')

  fab.env.git.pull()
  fab.env.git.create_release_commit()
  fab.env.git.push()


@fab.task
def deploy_apply_files():
  fab.require('git')

  fab.env.git.switch_release()


@fab.task
def deploy_files():
  fab.execute(deploy_push_files)
  fab.execute(deploy_apply_files)


@fab.task
def deploy(*args):
  fab.require('git')

  # prepare
  fab.execute(deploy_files)
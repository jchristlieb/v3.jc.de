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
# Tasks

# Deployment

def _deploy_git_factory():
  import fabdeploit

  class GitFilter(fabdeploit.GitFilter):
    def filter(self):

      for filename in (
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
    remote_repository_path='/home/www/p485630/html/jc',  # get this ready
    release_branch='staging',
  )

  _deploy_base_env()
  fab.env.hosts = ['escaperoom-dillingen']


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
def deploy(*args):
  fab.require('git')

  fab.execute(deploy_push_files)
  fab.execute(deploy_apply_files)



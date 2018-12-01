<?php

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     *
     * @return void
     */
    public function run()
    {
        // $this->call(UsersTableSeeder::class);

        // Create a default user
        factory(\App\User::class)->create([
            'email' => 'admin@admin.com',
            'password' => bcrypt('secret')
        ]);
    }
}

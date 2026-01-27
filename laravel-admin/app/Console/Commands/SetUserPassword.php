<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;

class SetUserPassword extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'user:set-password {email} {password}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Set password for a user';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $email = $this->argument('email');
        $password = $this->argument('password');

        $user = \App\Models\User::where('email', $email)->first();

        if (!$user) {
            $this->error("User with email {$email} not found");
            return 1;
        }

        $user->password_hash = password_hash($password, PASSWORD_BCRYPT);
        $user->save();

        $this->info("Password updated successfully for {$email}");
        $this->line("Hash: {$user->password_hash}");

        return 0;
    }
}

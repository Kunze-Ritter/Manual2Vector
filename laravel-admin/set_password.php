<?php

require __DIR__.'/vendor/autoload.php';

$app = require_once __DIR__.'/bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

$user = App\Models\User::where('email', 'test@example.com')->first();

if ($user) {
    $user->password_hash = password_hash('admin123', PASSWORD_BCRYPT);
    $user->save();
    echo "Password updated successfully for {$user->email}\n";
    echo "New hash: {$user->password_hash}\n";
} else {
    echo "User not found\n";
}

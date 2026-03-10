<?php

namespace App\Filament\Resources\Users\Schemas;

use App\Enums\UserRole;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Schema;

class UserForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                TextInput::make('username')
                    ->label('Benutzername')
                    ->required()
                    ->maxLength(100),

                TextInput::make('first_name')
                    ->label('Vorname')
                    ->maxLength(100),

                TextInput::make('last_name')
                    ->label('Nachname')
                    ->maxLength(100),

                TextInput::make('email')
                    ->label('E-Mail')
                    ->email()
                    ->required()
                    ->maxLength(255),

                Select::make('role')
                    ->label('Rolle')
                    ->options(UserRole::options())
                    ->required()
                    ->default(UserRole::Editor->value),

                TextInput::make('password')
                    ->label('Passwort')
                    ->password()
                    ->revealable()
                    ->required(fn (string $operation): bool => $operation === 'create')
                    ->dehydrated(fn ($state): bool => filled($state)),
            ]);
    }
}

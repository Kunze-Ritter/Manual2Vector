<?php

namespace App\Filament\Resources\Settings;

use App\Filament\Resources\Settings\Pages\ManageSettings;
use BackedEnum;
use Filament\Resources\Resource;
use UnitEnum;

class SettingsResource extends Resource
{
    protected static ?string $model = null;

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-cog-6-tooth';

    protected static string|UnitEnum|null $navigationGroup = 'Services';

    protected static ?string $navigationLabel = 'Einstellungen';

    protected static ?int $navigationSort = 3;

    protected static ?string $label = 'Settings';

    protected static ?string $pluralLabel = 'Settings';

    public static function getPages(): array
    {
        return [
            'index' => ManageSettings::route('/'),
        ];
    }

    public static function canViewAny(): bool
    {
        $user = auth()->user();

        if (! $user) {
            return false;
        }

        if (method_exists($user, 'isAdmin')) {
            return $user->isAdmin();
        }

        return false;
    }
}

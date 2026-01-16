<?php

namespace App\Filament\Resources\Monitoring;

use App\Filament\Resources\Monitoring\AlertConfigurationResource\Pages;
use App\Filament\Resources\Monitoring\AlertConfigurationResource\Schemas\AlertConfigurationForm;
use App\Filament\Resources\Monitoring\AlertConfigurationResource\Tables\AlertConfigurationsTable;
use App\Models\AlertConfiguration;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Tables\Table;

class AlertConfigurationResource extends Resource
{
    protected static ?string $model = AlertConfiguration::class;

    protected static ?string $navigationGroup = 'Monitoring';

    protected static ?string $navigationLabel = 'Alert-Konfigurationen';

    protected static ?string $navigationIcon = 'heroicon-o-bell-alert';

    protected static ?int $navigationSort = 2;

    protected static ?string $recordTitleAttribute = 'rule_name';

    public static function form(Schema $schema): Schema
    {
        return AlertConfigurationForm::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return AlertConfigurationsTable::configure($table);
    }

    public static function getRelations(): array
    {
        return [];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListAlertConfigurations::route('/'),
            'create' => Pages\CreateAlertConfiguration::route('/create'),
            'edit' => Pages\EditAlertConfiguration::route('/{record}/edit'),
        ];
    }
}

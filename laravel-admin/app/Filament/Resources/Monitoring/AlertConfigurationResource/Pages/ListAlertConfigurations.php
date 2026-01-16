<?php

namespace App\Filament\Resources\Monitoring\AlertConfigurationResource\Pages;

use App\Filament\Resources\Monitoring\AlertConfigurationResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListAlertConfigurations extends ListRecords
{
    protected static string $resource = AlertConfigurationResource::class;

    protected function getHeaderActions(): array
    {
        return [
            CreateAction::make(),
        ];
    }
}

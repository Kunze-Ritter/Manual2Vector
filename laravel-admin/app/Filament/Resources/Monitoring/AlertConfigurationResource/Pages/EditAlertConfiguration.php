<?php

namespace App\Filament\Resources\Monitoring\AlertConfigurationResource\Pages;

use App\Filament\Resources\Monitoring\AlertConfigurationResource;
use Filament\Actions\DeleteAction;
use Filament\Resources\Pages\EditRecord;

class EditAlertConfiguration extends EditRecord
{
    protected static string $resource = AlertConfigurationResource::class;

    protected function getHeaderActions(): array
    {
        return [
            DeleteAction::make(),
        ];
    }
}

<?php

namespace App\Filament\Resources\Monitoring\AlertConfigurationResource\Pages;

use App\Filament\Resources\Monitoring\AlertConfigurationResource;
use Filament\Resources\Pages\CreateRecord;

class CreateAlertConfiguration extends CreateRecord
{
    protected static string $resource = AlertConfigurationResource::class;

    protected function mutateFormDataBeforeCreate(array $data): array
    {
        $data['created_by'] = auth()->id();

        return $data;
    }
}

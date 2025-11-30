<?php

namespace App\Filament\Resources\ProductSeries\Pages;

use App\Filament\Resources\ProductSeries\ProductSeriesResource;
use Filament\Actions\DeleteAction;
use Filament\Resources\Pages\EditRecord;

class EditProductSeries extends EditRecord
{
    protected static string $resource = ProductSeriesResource::class;

    protected function getHeaderActions(): array
    {
        return [
            DeleteAction::make(),
        ];
    }
}

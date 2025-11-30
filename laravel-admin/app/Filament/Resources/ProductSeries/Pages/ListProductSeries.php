<?php

namespace App\Filament\Resources\ProductSeries\Pages;

use App\Filament\Resources\ProductSeries\ProductSeriesResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListProductSeries extends ListRecords
{
    protected static string $resource = ProductSeriesResource::class;

    protected function getHeaderActions(): array
    {
        return [
            CreateAction::make(),
        ];
    }
}

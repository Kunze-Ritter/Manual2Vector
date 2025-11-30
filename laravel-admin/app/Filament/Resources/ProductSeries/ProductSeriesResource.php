<?php

namespace App\Filament\Resources\ProductSeries;

use App\Filament\Resources\ProductSeries\Pages\CreateProductSeries;
use App\Filament\Resources\ProductSeries\Pages\EditProductSeries;
use App\Filament\Resources\ProductSeries\Pages\ListProductSeries;
use App\Filament\Resources\ProductSeries\Schemas\ProductSeriesForm;
use App\Filament\Resources\ProductSeries\Tables\ProductSeriesTable;
use App\Models\ProductSeries;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Schemas\Schema;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Table;
use UnitEnum;

class ProductSeriesResource extends Resource
{
    protected static ?string $model = ProductSeries::class;

    public static UnitEnum|string|null $navigationGroup = 'Produkte';

    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedRectangleStack;

    protected static ?string $recordTitleAttribute = 'series_name';

    public static function form(Schema $schema): Schema
    {
        return ProductSeriesForm::configure($schema);
    }

    public static function table(Table $table): Table
    {
        return ProductSeriesTable::configure($table);
    }

    public static function getRelations(): array
    {
        return [
            // Relations können später ergänzt werden (z.B. Products Relation Manager)
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => ListProductSeries::route('/'),
            'create' => CreateProductSeries::route('/create'),
            'edit' => EditProductSeries::route('/{record}/edit'),
        ];
    }
}

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

    protected static UnitEnum|string|null $navigationGroup = 'Data';

    protected static ?string $navigationLabel = 'Produktserien';

    protected static string|BackedEnum|null $navigationIcon = 'heroicon-o-rectangle-stack';

    protected static ?int $navigationSort = 4;

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

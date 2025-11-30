<?php

namespace App\Filament\Resources\ProductSeries\Schemas;

use Filament\Forms\Components\DatePicker;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Schemas\Schema;

class ProductSeriesForm
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Select::make('manufacturer_id')
                    ->label('Hersteller')
                    ->relationship('manufacturer', 'name')
                    ->searchable()
                    ->preload()
                    ->required(),

                TextInput::make('series_name')
                    ->label('Serienname')
                    ->required()
                    ->maxLength(100),

                TextInput::make('series_code')
                    ->label('Seriencode')
                    ->maxLength(50),

                DatePicker::make('launch_date')
                    ->label('Launch-Datum'),

                DatePicker::make('end_of_life_date')
                    ->label('End-of-Life-Datum'),

                TextInput::make('target_market')
                    ->label('Zielmarkt')
                    ->maxLength(100),

                TextInput::make('price_range')
                    ->label('Preisspanne')
                    ->maxLength(50),

                Textarea::make('series_description')
                    ->label('Beschreibung')
                    ->rows(3),

                TextInput::make('marketing_name')
                    ->label('Marketing-Name')
                    ->maxLength(150),

                Select::make('successor_series_id')
                    ->label('Nachfolgeserie')
                    ->relationship('successorSeries', 'series_name')
                    ->searchable()
                    ->preload(),

                Textarea::make('model_pattern')
                    ->label('Modell-Pattern')
                    ->rows(2),
            ]);
    }
}

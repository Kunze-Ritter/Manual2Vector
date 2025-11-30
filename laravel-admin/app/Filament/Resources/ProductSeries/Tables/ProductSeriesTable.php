<?php

namespace App\Filament\Resources\ProductSeries\Tables;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;

class ProductSeriesTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('manufacturer.name')
                    ->label('Hersteller')
                    ->searchable()
                    ->sortable(),

                TextColumn::make('series_name')
                    ->label('Serie')
                    ->searchable()
                    ->sortable(),

                TextColumn::make('series_code')
                    ->label('Code')
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('target_market')
                    ->label('Zielmarkt')
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('price_range')
                    ->label('Preisspanne')
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('launch_date')
                    ->label('Launch')
                    ->date()
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('end_of_life_date')
                    ->label('EOL')
                    ->date()
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('marketing_name')
                    ->label('Marketing-Name')
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('created_at')
                    ->label('Erstellt am')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('updated_at')
                    ->label('Aktualisiert am')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                // vorerst keine speziellen Filter
            ])
            ->recordActions([
                EditAction::make(),
            ])
            ->toolbarActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}

<?php

namespace App\Filament\Resources\Manufacturers\RelationManagers;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;

class ErrorCodesRelationManager extends RelationManager
{
    protected static string $relationship = 'errorCodes';

    protected static ?string $recordTitleAttribute = 'error_code';

    public function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('error_code')
                    ->label('Code')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('error_description')
                    ->label('Description')
                    ->limit(50)
                    ->searchable(),
                Tables\Columns\TextColumn::make('severity_level')
                    ->label('Severity')
                    ->badge(),
                Tables\Columns\BooleanColumn::make('requires_technician')
                    ->label('Technician'),
                Tables\Columns\BooleanColumn::make('requires_parts')
                    ->label('Parts'),
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Created')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('severity_level')
                    ->options(['low' => 'Low', 'medium' => 'Medium', 'high' => 'High', 'critical' => 'Critical']),
            ])
            ->headerActions([
                // Read-only - extracted from documents
            ])
            ->actions([
                ViewAction::make(),
                EditAction::make(),
            ])
            ->bulkActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}

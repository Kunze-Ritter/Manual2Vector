<?php

namespace App\Filament\Resources\Manufacturers\RelationManagers;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;

class DocumentsRelationManager extends RelationManager
{
    protected static string $relationship = 'documents';

    protected static ?string $recordTitleAttribute = 'filename';

    public function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('filename')
                    ->label('Filename')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('document_type')
                    ->label('Type')
                    ->sortable(),
                Tables\Columns\TextColumn::make('language')
                    ->label('Language')
                    ->sortable(),
                Tables\Columns\TextColumn::make('processing_status')
                    ->label('Status')
                    ->badge(),
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Created')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('document_type')
                    ->options(['manual' => 'Manual', 'datasheet' => 'Datasheet', 'service_manual' => 'Service Manual']),
                Tables\Filters\SelectFilter::make('processing_status')
                    ->options(['pending' => 'Pending', 'processing' => 'Processing', 'completed' => 'Completed', 'failed' => 'Failed']),
            ])
            ->headerActions([
                // Read-only for manufacturers - documents are created via upload
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

<?php

namespace App\Filament\Resources\Monitoring\AlertConfigurationResource\Tables;

use Filament\Tables\Actions\Action;
use Filament\Tables\Actions\BulkActionGroup;
use Filament\Tables\Actions\DeleteBulkAction;
use Filament\Tables\Actions\EditAction;
use Filament\Tables\Columns\IconColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Filters\TernaryFilter;
use Filament\Tables\Table;

class AlertConfigurationsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                IconColumn::make('is_enabled')
                    ->label('Status')
                    ->boolean()
                    ->tooltip(fn ($state) => $state ? 'Aktiviert' : 'Deaktiviert'),

                TextColumn::make('rule_name')
                    ->label('Regelname')
                    ->searchable()
                    ->sortable(),

                TextColumn::make('description')
                    ->label('Beschreibung')
                    ->limit(50)
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('error_types')
                    ->label('Fehlertypen')
                    ->badge()
                    ->formatStateUsing(fn ($state) => is_array($state) ? implode(', ', $state) : $state),

                TextColumn::make('stages')
                    ->label('Stages')
                    ->badge()
                    ->formatStateUsing(fn ($state) => is_array($state) ? implode(', ', $state) : $state),

                TextColumn::make('severity_threshold')
                    ->label('Schweregrad')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'critical', 'high' => 'danger',
                        'medium' => 'warning',
                        'low' => 'info',
                        default => 'gray',
                    }),

                TextColumn::make('error_count_threshold')
                    ->label('Fehleranzahl')
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('email_recipients')
                    ->label('E-Mail-Empfänger')
                    ->formatStateUsing(fn ($state) => is_array($state) ? count($state) : 0)
                    ->toggleable(isToggledHiddenByDefault: true),

                TextColumn::make('created_at')
                    ->label('Erstellt am')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                TernaryFilter::make('is_enabled')
                    ->label('Aktiviert'),

                SelectFilter::make('severity_threshold')
                    ->label('Schweregrad')
                    ->options([
                        'low' => 'Low',
                        'medium' => 'Medium',
                        'high' => 'High',
                        'critical' => 'Critical',
                    ]),

                SelectFilter::make('stages')
                    ->label('Stage')
                    ->options([
                        'classification' => 'Classification',
                        'chunking' => 'Chunking',
                        'embedding' => 'Embedding',
                        'link_enrichment' => 'Link Enrichment',
                        'image_extraction' => 'Image Extraction',
                        'error_code_extraction' => 'Error Code Extraction',
                    ])
                    ->searchable()
                    ->query(function ($query, $state) {
                        if (filled($state['value'])) {
                            $query->whereRaw('stages @> ARRAY[?]::varchar[]', [$state['value']]);
                        }
                    }),
            ])
            ->actions([
                EditAction::make(),

                Action::make('toggle')
                    ->label('Aktivieren/Deaktivieren')
                    ->icon('heroicon-o-power')
                    ->action(function ($record) {
                        $record->update(['is_enabled' => !$record->is_enabled]);
                    }),
            ])
            ->bulkActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}

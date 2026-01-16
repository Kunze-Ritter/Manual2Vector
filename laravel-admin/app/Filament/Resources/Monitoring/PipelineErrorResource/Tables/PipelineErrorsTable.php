<?php

namespace App\Filament\Resources\Monitoring\PipelineErrorResource\Tables;

use App\Filament\Resources\Monitoring\PipelineErrorResource;
use App\Models\PipelineError;
use App\Services\BackendApiService;
use Filament\Forms\Components\DatePicker;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Tables;
use Filament\Tables\Columns\IconColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\Filter;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Facades\Log;

class PipelineErrorsTable
{
    public static function make(Table $table): Table
    {
        return $table
            ->columns([
                IconColumn::make('status')
                    ->label('')
                    ->icon(fn (PipelineError $record): string => match($record->status) {
                        'pending' => 'heroicon-o-x-circle',
                        'retrying' => 'heroicon-o-arrow-path',
                        'resolved' => 'heroicon-o-check-circle',
                        default => 'heroicon-o-exclamation-triangle',
                    })
                    ->color(fn (PipelineError $record): string => 
                        PipelineErrorResource::getStatusBadgeColor($record->status)
                    )
                    ->tooltip(fn (PipelineError $record): string => ucfirst($record->status)),

                TextColumn::make('created_at')
                    ->label('Timestamp')
                    ->dateTime('Y-m-d H:i:s')
                    ->sortable()
                    ->searchable(),

                TextColumn::make('document.id')
                    ->label('Dokument-ID')
                    ->limit(8)
                    ->copyable()
                    ->copyMessage('Dokument-ID kopiert')
                    ->tooltip(fn (PipelineError $record): ?string => $record->document?->id)
                    ->url(fn (PipelineError $record): ?string => 
                        $record->document_id 
                            ? route('filament.kradmin.resources.documents.documents.edit', $record->document_id)
                            : null
                    )
                    ->color('primary'),

                TextColumn::make('stage_name')
                    ->label('Stage')
                    ->sortable()
                    ->searchable()
                    ->badge(),

                TextColumn::make('error_type')
                    ->label('Fehlertyp')
                    ->badge()
                    ->color(fn (PipelineError $record): string => match($record->severity ?? 'medium') {
                        'critical', 'high' => 'danger',
                        'medium' => 'warning',
                        'low' => 'info',
                        default => 'gray',
                    })
                    ->searchable(),

                TextColumn::make('retry_count')
                    ->label('Retries')
                    ->formatStateUsing(fn (PipelineError $record): string => 
                        "{$record->retry_count}/{$record->max_retries}"
                    )
                    ->sortable(),

                TextColumn::make('error_message')
                    ->label('Nachricht')
                    ->limit(50)
                    ->tooltip(fn (PipelineError $record): string => $record->error_message ?? '')
                    ->searchable()
                    ->wrap(),
            ])
            ->filters([
                Filter::make('created_at')
                    ->form([
                        DatePicker::make('created_from')
                            ->label('Von'),
                        DatePicker::make('created_until')
                            ->label('Bis'),
                    ])
                    ->query(function (Builder $query, array $data): Builder {
                        return $query
                            ->when(
                                $data['created_from'],
                                fn (Builder $query, $date): Builder => $query->whereDate('created_at', '>=', $date),
                            )
                            ->when(
                                $data['created_until'],
                                fn (Builder $query, $date): Builder => $query->whereDate('created_at', '<=', $date),
                            );
                    })
                    ->indicateUsing(function (array $data): array {
                        $indicators = [];
                        if ($data['created_from'] ?? null) {
                            $indicators[] = Tables\Filters\Indicator::make('Von ' . \Carbon\Carbon::parse($data['created_from'])->toFormattedDateString())
                                ->removeField('created_from');
                        }
                        if ($data['created_until'] ?? null) {
                            $indicators[] = Tables\Filters\Indicator::make('Bis ' . \Carbon\Carbon::parse($data['created_until'])->toFormattedDateString())
                                ->removeField('created_until');
                        }
                        return $indicators;
                    }),

                SelectFilter::make('stage_name')
                    ->label('Stage')
                    ->options([
                        'classification' => 'Classification',
                        'chunking' => 'Chunking',
                        'embedding' => 'Embedding',
                        'link_enrichment' => 'Link Enrichment',
                        'image_extraction' => 'Image Extraction',
                        'table_extraction' => 'Table Extraction',
                        'video_extraction' => 'Video Extraction',
                        'error_code_extraction' => 'Error Code Extraction',
                        'solution_extraction' => 'Solution Extraction',
                    ])
                    ->searchable(),

                SelectFilter::make('error_type')
                    ->label('Fehlertyp')
                    ->options([
                        'TimeoutError' => 'Timeout',
                        'ConnectionError' => 'Connection Error',
                        'RateLimitError' => 'Rate Limit',
                        'ParseError' => 'Parse Error',
                        'ValidationError' => 'Validation Error',
                        'APIError' => 'API Error',
                        'DatabaseError' => 'Database Error',
                    ])
                    ->searchable(),

                SelectFilter::make('status')
                    ->label('Status')
                    ->options([
                        'pending' => 'Active',
                        'retrying' => 'Retrying',
                        'resolved' => 'Resolved',
                    ])
                    ->default('pending'),

                Filter::make('document_id')
                    ->form([
                        TextInput::make('document_id')
                            ->label('Dokument-ID')
                            ->placeholder('UUID eingeben'),
                    ])
                    ->query(function (Builder $query, array $data): Builder {
                        return $query->when(
                            $data['document_id'],
                            fn (Builder $query, $id): Builder => $query->where('document_id', 'like', "%{$id}%"),
                        );
                    }),
            ])
            ->actions([
                Tables\Actions\ViewAction::make(),

                Tables\Actions\Action::make('retry')
                    ->label('Retry')
                    ->icon('heroicon-o-arrow-path')
                    ->color('warning')
                    ->visible(fn (PipelineError $record): bool => $record->status !== 'resolved')
                    ->disabled(fn () => !PipelineErrorResource::getBackendApiService()->validateConfiguration())
                    ->requiresConfirmation()
                    ->modalHeading('Stage erneut versuchen')
                    ->modalDescription('Möchten Sie diese Stage wirklich erneut versuchen?')
                    ->action(function (PipelineError $record) {
                        try {
                            $service = PipelineErrorResource::getBackendApiService();
                            $result = $service->retryStage($record->document_id, $record->stage_name);

                            if ($result['success'] === true) {
                                Notification::make()
                                    ->title('Stage wird erneut verarbeitet')
                                    ->body("Stage '{$record->stage_name}' wird für Dokument {$record->document_id} erneut verarbeitet.")
                                    ->success()
                                    ->send();
                            } else {
                                Notification::make()
                                    ->title('Retry fehlgeschlagen')
                                    ->body($result['error'] ?? 'Unbekannter Fehler beim Retry-Versuch.')
                                    ->danger()
                                    ->send();
                            }
                        } catch (\Exception $e) {
                            Log::error('Pipeline retry action failed', [
                                'error_id' => $record->error_id,
                                'document_id' => $record->document_id,
                                'stage_name' => $record->stage_name,
                                'exception' => $e->getMessage(),
                            ]);

                            Notification::make()
                                ->title('Retry fehlgeschlagen')
                                ->body('Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.')
                                ->danger()
                                ->send();
                        }
                    })
                    ->after(fn ($action) => $action->getLivewire()->dispatch('$refresh')),

                Tables\Actions\Action::make('resolve')
                    ->label('Als gelöst markieren')
                    ->icon('heroicon-o-check-circle')
                    ->color('success')
                    ->visible(fn (PipelineError $record): bool => $record->status !== 'resolved')
                    ->form([
                        Textarea::make('resolution_notes')
                            ->label('Lösungsnotizen')
                            ->required()
                            ->maxLength(1000)
                            ->rows(4),
                    ])
                    ->action(function (PipelineError $record, array $data) {
                        // Update local database first
                        $record->update([
                            'status' => 'resolved',
                            'resolved_at' => now(),
                            'resolved_by' => auth()->id(),
                            'resolution_notes' => $data['resolution_notes'],
                        ]);

                        // Sync with backend API
                        try {
                            $service = PipelineErrorResource::getBackendApiService();
                            $result = $service->markErrorResolved(
                                $record->error_id,
                                auth()->id(),
                                $data['resolution_notes']
                            );

                            if ($result['success'] === true) {
                                Notification::make()
                                    ->title('Fehler als gelöst markiert')
                                    ->body('Fehler wurde lokal und im Backend als gelöst markiert.')
                                    ->success()
                                    ->send();
                            } else {
                                Log::warning('Backend sync failed for resolved error', [
                                    'error_id' => $record->error_id,
                                    'error' => $result['error'] ?? 'Unknown error',
                                ]);

                                Notification::make()
                                    ->title('Fehler lokal markiert')
                                    ->body('Fehler lokal markiert, aber Backend-Synchronisation fehlgeschlagen: ' . ($result['error'] ?? 'Unbekannter Fehler'))
                                    ->warning()
                                    ->send();
                            }
                        } catch (\Exception $e) {
                            Log::error('Exception during backend sync for resolved error', [
                                'error_id' => $record->error_id,
                                'exception' => $e->getMessage(),
                            ]);

                            Notification::make()
                                ->title('Fehler lokal markiert')
                                ->body('Fehler lokal markiert, aber Backend-Synchronisation fehlgeschlagen.')
                                ->warning()
                                ->send();
                        }
                    })
                    ->after(fn ($action) => $action->getLivewire()->dispatch('$refresh')),

                Tables\Actions\Action::make('copyErrorId')
                    ->label('Error-ID kopieren')
                    ->icon('heroicon-o-clipboard')
                    ->action(function (PipelineError $record) {
                        return $record->error_id;
                    })
                    ->successNotificationTitle('Error-ID kopiert')
                    ->extraAttributes(function (PipelineError $record) {
                        return [
                            'x-on:click' => 'navigator.clipboard.writeText("' . e($record->error_id) . '")',
                        ];
                    }),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\BulkAction::make('markResolved')
                        ->label('Als gelöst markieren')
                        ->icon('heroicon-o-check-circle')
                        ->color('success')
                        ->requiresConfirmation()
                        ->form([
                            Textarea::make('resolution_notes')
                                ->label('Lösungsnotizen')
                                ->required()
                                ->maxLength(1000)
                                ->rows(4),
                        ])
                        ->action(function ($records, array $data) {
                            $service = PipelineErrorResource::getBackendApiService();
                            $localCount = 0;
                            $backendSyncedCount = 0;
                            $backendFailedCount = 0;

                            $records->each(function (PipelineError $record) use ($data, $service, &$localCount, &$backendSyncedCount, &$backendFailedCount) {
                                // Update local database
                                $record->update([
                                    'status' => 'resolved',
                                    'resolved_at' => now(),
                                    'resolved_by' => auth()->id(),
                                    'resolution_notes' => $data['resolution_notes'],
                                ]);
                                $localCount++;

                                // Sync with backend
                                try {
                                    $result = $service->markErrorResolved(
                                        $record->error_id,
                                        auth()->id(),
                                        $data['resolution_notes']
                                    );

                                    if ($result['success'] === true) {
                                        $backendSyncedCount++;
                                    } else {
                                        $backendFailedCount++;
                                        Log::warning('Bulk resolve backend sync failed', [
                                            'error_id' => $record->error_id,
                                            'error' => $result['error'] ?? 'Unknown error',
                                        ]);
                                    }
                                } catch (\Exception $e) {
                                    $backendFailedCount++;
                                    Log::error('Bulk resolve backend sync exception', [
                                        'error_id' => $record->error_id,
                                        'exception' => $e->getMessage(),
                                    ]);
                                }
                            });

                            // Show notification based on results
                            $notificationBody = "{$localCount} Fehler lokal markiert, {$backendSyncedCount} Backend-synchronisiert";
                            if ($backendFailedCount > 0) {
                                $notificationBody .= ", {$backendFailedCount} Fehler bei Backend-Sync";
                            }

                            $notificationColor = 'success';
                            if ($backendFailedCount === $localCount) {
                                $notificationColor = 'danger';
                            } elseif ($backendFailedCount > 0) {
                                $notificationColor = 'warning';
                            }

                            Notification::make()
                                ->title('Fehler als gelöst markiert')
                                ->body($notificationBody)
                                ->color($notificationColor)
                                ->send();
                        }),
                ]),
            ])
            ->defaultSort('created_at', 'desc')
            ->poll('15s');
    }
}

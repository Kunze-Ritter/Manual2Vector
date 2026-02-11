<?php

namespace App\Filament\Resources\Documents\Tables;

use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\BulkAction;
use Filament\Forms\Components\Select;
use Filament\Notifications\Notification;
use Filament\Tables\Columns\IconColumn;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Filters\Filter;
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Filters\TernaryFilter;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Support\Collection;
use App\Services\KraiEngineService;

class DocumentsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('filename')
                    ->label('Dateiname')
                    ->searchable()
                    ->sortable(),

                TextColumn::make('document_type')
                    ->label('Typ')
                    ->sortable(),

                TextColumn::make('language')
                    ->label('Sprache')
                    ->sortable(),

                TextColumn::make('manufacturer')
                    ->label('Hersteller')
                    ->searchable()
                    ->sortable(),

                TextColumn::make('series')
                    ->label('Serie')
                    ->searchable()
                    ->sortable(),

                TextColumn::make('processing_status')
                    ->label('Status')
                    ->sortable(),

                TextColumn::make('stage_status')
                    ->label('Stage Status')
                    ->getStateUsing(function ($record) {
                        $stageStatus = $record->stage_status ?? [];
                        if (empty($stageStatus)) {
                            return 'Keine Stages';
                        }
                        
                        $completed = collect($stageStatus)->filter(function ($status) {
                            return $status === 'completed';
                        })->count();
                        $failed = collect($stageStatus)->filter(function ($status) {
                            return $status === 'failed';
                        })->count();
                        $total = count($stageStatus);
                        
                        return sprintf('%d/%d ✓ | %d ✗', $completed, $total, $failed);
                    })
                    ->badge()
                    ->color(function ($record) {
                        $stageStatus = $record->stage_status ?? [];
                        if (empty($stageStatus)) return 'gray';
                        
                        $failed = collect($stageStatus)->filter(function ($status) {
                            return $status === 'failed';
                        })->count();
                        if ($failed > 0) return 'danger';
                        
                        $completed = collect($stageStatus)->filter(function ($status) {
                            return $status === 'completed';
                        })->count();
                        $total = count($stageStatus);
                        
                        if ($completed === $total) return 'success';
                        return 'warning';
                    })
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: false),

                TextColumn::make('extracted_metadata')
                    ->label('Hochgeladen von')
                    ->getStateUsing(function ($record) {
                        $metadata = $record->extracted_metadata ?? [];

                        return data_get($metadata, 'upload.uploaded_by.username');
                    })
                    ->toggleable(isToggledHiddenByDefault: true),

                IconColumn::make('manual_review_required')
                    ->label('Review erforderlich')
                    ->boolean(),

                IconColumn::make('manual_review_completed')
                    ->label('Review fertig')
                    ->boolean(),

                TextColumn::make('priority_level')
                    ->label('Prio')
                    ->sortable(),

                TextColumn::make('created_at')
                    ->label('Erstellt am')
                    ->dateTime()
                    ->sortable(),

                TextColumn::make('updated_at')
                    ->label('Aktualisiert am')
                    ->dateTime()
                    ->sortable(),
            ])
            ->filters([
                SelectFilter::make('document_type')
                    ->label('Dokumenttyp')
                    ->options([
                        'service_manual' => 'Service Manual',
                        'parts_catalog' => 'Parts Catalog',
                        'user_guide' => 'User Guide',
                    ]),

                SelectFilter::make('processing_status')
                    ->label('Status')
                    ->options([
                        'pending' => 'Pending',
                        'uploaded' => 'Uploaded',
                        'processing' => 'Processing',
                        'completed' => 'Completed',
                        'failed' => 'Failed',
                    ]),

                TernaryFilter::make('manual_review_required')
                    ->label('Review erforderlich'),

                TernaryFilter::make('manual_review_completed')
                    ->label('Review fertig'),

                Filter::make('uploader')
                    ->label('Uploader')
                    ->form([
                        \Filament\Forms\Components\TextInput::make('username')
                            ->label('Username')
                            ->placeholder('z.B. kradmin'),
                    ])
                    ->query(function (Builder $query, array $data): Builder {
                        $username = $data['username'] ?? null;

                        if (! $username) {
                            return $query;
                        }

                        return $query->whereRaw(
                            "extracted_metadata->'upload'->'uploaded_by'->>'username' ILIKE ?",
                            ['%' . $username . '%']
                        );
                    }),
            ])
            ->recordActions([
                EditAction::make(),
            ])
            ->toolbarActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                    
                    BulkAction::make('smartProcessBulk')
                        ->label('Smart verarbeiten')
                        ->icon('heroicon-o-sparkles')
                        ->action(function (Collection $records) {
                            $service = app(KraiEngineService::class);
                            $stages = config('krai.default_stages', []);
                            $success = 0;
                            $failed = 0;

                            foreach ($records as $record) {
                                $result = $service->processMultipleStages($record->id, $stages, true);
                                if ($result['success'] && ($result['failed'] ?? 0) === 0) {
                                    $success++;
                                } else {
                                    $failed++;
                                }
                            }

                            $notification = Notification::make()
                                ->title('Smart-Verarbeitung abgeschlossen')
                                ->body(sprintf('%d erfolgreich, %d fehlgeschlagen', $success, $failed));

                            if ($failed === 0) {
                                $notification->success();
                            } elseif ($success === 0) {
                                $notification->danger();
                            } else {
                                $notification->warning();
                            }

                            $notification->send();
                        })
                        ->deselectRecordsAfterCompletion(),

                    BulkAction::make('processStageBulk')
                        ->label('Stage verarbeiten')
                        ->icon('heroicon-o-play')
                        ->form([
                            Select::make('stage')
                                ->label('Stage auswählen')
                                ->options(collect(config('krai.stages'))->mapWithKeys(fn($stage, $key) => [$key => $stage['label']]))
                                ->required()
                        ])
                        ->action(function (Collection $records, array $data) {
                            $service = app(KraiEngineService::class);
                            $stage = $data['stage'];
                            $success = 0;
                            $failed = 0;
                            
                            foreach ($records as $record) {
                                $result = $service->processStage($record->id, $stage);
                                if ($result['success']) {
                                    $success++;
                                } else {
                                    $failed++;
                                }
                            }
                            
                            // Determine notification color based on results
                            $notification = Notification::make()
                                ->title('Stage-Verarbeitung abgeschlossen')
                                ->body(sprintf('%d erfolgreich, %d fehlgeschlagen', $success, $failed));
                            
                            if ($failed === 0) {
                                $notification->success();
                            } elseif ($success === 0) {
                                $notification->danger();
                            } else {
                                $notification->warning();
                            }
                            
                            $notification->send();
                        })
                        ->deselectRecordsAfterCompletion(),
                    
                    BulkAction::make('generateThumbnailsBulk')
                        ->label('Thumbnails generieren')
                        ->icon('heroicon-o-photo')
                        ->action(function (Collection $records) {
                            $service = app(KraiEngineService::class);
                            $success = 0;
                            $failed = 0;
                            
                            foreach ($records as $record) {
                                $result = $service->generateThumbnail($record->id);
                                if ($result['success']) {
                                    $success++;
                                } else {
                                    $failed++;
                                }
                            }
                            
                            // Determine notification color based on results
                            $notification = Notification::make()
                                ->title('Thumbnail-Generierung abgeschlossen')
                                ->body(sprintf('%d erfolgreich, %d fehlgeschlagen', $success, $failed));
                            
                            if ($failed === 0) {
                                $notification->success();
                            } elseif ($success === 0) {
                                $notification->danger();
                            } else {
                                $notification->warning();
                            }
                            
                            $notification->send();
                        })
                        ->deselectRecordsAfterCompletion(),
                ]),
            ]);
    }
}

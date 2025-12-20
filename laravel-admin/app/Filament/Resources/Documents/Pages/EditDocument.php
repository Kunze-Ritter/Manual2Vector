<?php

namespace App\Filament\Resources\Documents\Pages;

use App\Filament\Resources\Documents\DocumentResource;
use App\Models\Manufacturer;
use App\Services\KraiEngineService;
use Filament\Actions\Action;
use Filament\Actions\DeleteAction;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\CheckboxList;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\EditRecord;
use Illuminate\Support\Facades\Http;

class EditDocument extends EditRecord
{
    protected static string $resource = DocumentResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Action::make('viewStageStatus')
                ->label('Stage Status anzeigen')
                ->icon('heroicon-o-chart-bar')
                ->visible(function (): bool {
                    $user = auth()->user();

                    if (! $user) {
                        return false;
                    }

                    if (method_exists($user, 'canManageContent')) {
                        return $user->canManageContent();
                    }

                    return true;
                })
                ->modalHeading('Stage Verarbeitungsstatus')
                ->modalContent(function () {
                    $record = $this->getRecord();
                    $service = app(KraiEngineService::class);
                    $statusData = $service->getStageStatus($record->id);
                    
                    // Handle backend errors
                    if (!$statusData['success'] && isset($statusData['error'])) {
                        // Trigger danger notification for backend error
                        Notification::make()
                            ->title('Fehler beim Abrufen des Stage-Status')
                            ->body($statusData['error'])
                            ->danger()
                            ->send();
                        
                        // Return error view
                        return view('filament.components.stage-status-error', [
                            'error' => $statusData['error']
                        ]);
                    }
                    
                    // Handle case where request succeeded but data not found
                    if (!$statusData['found']) {
                        return view('filament.components.stage-status-empty');
                    }
                    
                    $stageStatus = $statusData['stage_status'];
                    $stages = config('krai.stages');
                    
                    return view('filament.components.stage-status-grid', [
                        'stageStatus' => $stageStatus,
                        'stages' => $stages
                    ]);
                })
                ->modalWidth('5xl')
                ->slideOver(),

            Action::make('checkStatus')
                ->label('Status prüfen')
                ->icon('heroicon-o-information-circle')
                ->visible(function (): bool {
                    $user = auth()->user();

                    if (! $user) {
                        return false;
                    }

                    if (method_exists($user, 'canManageContent')) {
                        return $user->canManageContent();
                    }

                    return true;
                })
                ->action(function (): void {
                    $record = $this->getRecord();
                    $service = app(KraiEngineService::class);

                    $result = $service->getDocumentStatus($record->id);
                    
                    if ($result['success']) {
                        $bodyLines = [];
                        $bodyLines[] = 'Dokumentenstatus: ' . $result['document_status'];
                        
                        if ($result['queue_position'] > 0 && $result['total_queue_items'] > 0) {
                            $bodyLines[] = 'Queue-Position: ' . $result['queue_position'] . ' von ' . $result['total_queue_items'];
                        }

                        Notification::make()
                            ->title('Dokumentenstatus')
                            ->body(implode("\n", $bodyLines))
                            ->success()
                            ->send();
                    } else {
                        Notification::make()
                            ->title('Statusabfrage fehlgeschlagen')
                            ->body($result['error'] ?? 'Der Dokumentenstatus konnte nicht geladen werden.')
                            ->danger()
                            ->send();
                    }
                }),

            Action::make('processSingleStage')
                ->label('Stage verarbeiten')
                ->icon('heroicon-o-play')
                ->visible(function (): bool {
                    $user = auth()->user();

                    if (! $user) {
                        return false;
                    }

                    if (method_exists($user, 'canManageContent')) {
                        return $user->canManageContent();
                    }

                    return true;
                })
                ->form([
                    Select::make('stage')
                        ->label('Stage auswählen')
                        ->options(collect(config('krai.stages'))->mapWithKeys(fn($stage, $key) => [$key => $stage['label']]))
                        ->required()
                        ->helperText('Wählen Sie eine einzelne Stage zur Verarbeitung')
                ])
                ->action(function (array $data): void {
                    $record = $this->getRecord();
                    $service = app(KraiEngineService::class);
                    
                    $result = $service->processStage($record->id, $data['stage']);
                    
                    if ($result['success']) {
                        Notification::make()
                            ->title('Stage erfolgreich verarbeitet')
                            ->body(sprintf('Stage "%s" wurde in %.2fs verarbeitet', config('krai.stages.'.$data['stage'].'.label'), $result['processing_time']))
                            ->success()
                            ->send();
                    } else {
                        Notification::make()
                            ->title('Stage-Verarbeitung fehlgeschlagen')
                            ->body($result['error'] ?? 'Unbekannter Fehler')
                            ->danger()
                            ->send();
                    }
                }),

            Action::make('processMultipleStages')
                ->label('Mehrere Stages verarbeiten')
                ->icon('heroicon-o-play-circle')
                ->visible(function (): bool {
                    $user = auth()->user();

                    if (! $user) {
                        return false;
                    }

                    if (method_exists($user, 'canManageContent')) {
                        return $user->canManageContent();
                    }

                    return true;
                })
                ->form([
                    CheckboxList::make('stages')
                        ->label('Stages auswählen')
                        ->options(collect(config('krai.stages'))->mapWithKeys(fn($stage, $key) => [$key => $stage['label']]))
                        ->columns(3)
                        ->required()
                        ->helperText('Wählen Sie mehrere Stages zur sequenziellen Verarbeitung'),
                    
                    \Filament\Forms\Components\Toggle::make('stop_on_error')
                        ->label('Bei Fehler stoppen')
                        ->default(true)
                        ->helperText('Verarbeitung bei erstem Fehler abbrechen')
                ])
                ->action(function (array $data): void {
                    $record = $this->getRecord();
                    $service = app(KraiEngineService::class);
                    
                    $result = $service->processMultipleStages(
                        $record->id, 
                        $data['stages'], 
                        $data['stop_on_error'] ?? true
                    );
                    
                    if ($result['success']) {
                        Notification::make()
                            ->title('Stages erfolgreich verarbeitet')
                            ->body(sprintf('%d von %d Stages erfolgreich (%.1f%%)', $result['successful'], $result['total_stages'], $result['success_rate'] * 100))
                            ->success()
                            ->send();
                    } else {
                        Notification::make()
                            ->title('Stage-Verarbeitung teilweise fehlgeschlagen')
                            ->body(sprintf('%d erfolgreich, %d fehlgeschlagen', $result['successful'], $result['failed']))
                            ->warning()
                            ->send();
                    }
                }),

            Action::make('processVideo')
                ->label('Video verarbeiten')
                ->icon('heroicon-o-video-camera')
                ->visible(function (): bool {
                    $user = auth()->user();

                    if (! $user) {
                        return false;
                    }

                    if (method_exists($user, 'canManageContent')) {
                        return $user->canManageContent();
                    }

                    return true;
                })
                ->form([
                    TextInput::make('video_url')
                        ->label('Video URL')
                        ->url()
                        ->required()
                        ->placeholder('https://www.youtube.com/watch?v=...')
                        ->helperText('YouTube, Vimeo oder Brightcove URL'),
                    
                    Select::make('manufacturer_select')
                        ->label('Hersteller (optional)')
                        ->options(fn () => Manufacturer::query()
                            ->orderBy('name')
                            ->pluck('name', 'id')
                            ->toArray()
                        )
                        ->searchable()
                        ->preload()
                        ->getSearchResultsUsing(fn (string $search) => Manufacturer::query()
                            ->where('name', 'like', "%{$search}%")
                            ->orderBy('name')
                            ->limit(50)
                            ->pluck('name', 'id')
                            ->toArray())
                ])
                ->action(function (array $data): void {
                    $record = $this->getRecord();
                    $service = app(KraiEngineService::class);
                    
                    $result = $service->processVideo(
                        $record->id, 
                        $data['video_url'], 
                        $data['manufacturer_select'] ?? null
                    );
                    
                    if ($result['success']) {
                        Notification::make()
                            ->title('Video erfolgreich verarbeitet')
                            ->body(sprintf('Video "%s" (%s) wurde verknüpft', $result['title'], $result['platform']))
                            ->success()
                            ->send();
                    } else {
                        Notification::make()
                            ->title('Video-Verarbeitung fehlgeschlagen')
                            ->body($result['error'] ?? 'Unbekannter Fehler')
                            ->danger()
                            ->send();
                    }
                }),

            Action::make('generateThumbnail')
                ->label('Thumbnail generieren')
                ->icon('heroicon-o-photo')
                ->visible(function (): bool {
                    $user = auth()->user();

                    if (! $user) {
                        return false;
                    }

                    if (method_exists($user, 'canManageContent')) {
                        return $user->canManageContent();
                    }

                    return true;
                })
                ->form([
                    TextInput::make('page')
                        ->label('Seite')
                        ->numeric()
                        ->default(0)
                        ->minValue(0)
                        ->helperText('Seitennummer (0 = erste Seite)'),
                    
                    Select::make('size')
                        ->label('Größe')
                        ->options([
                            '300x400' => 'Standard (300x400)',
                            '600x800' => 'Groß (600x800)',
                            '150x200' => 'Klein (150x200)'
                        ])
                        ->default('300x400')
                ])
                ->action(function (array $data): void {
                    $record = $this->getRecord();
                    $service = app(KraiEngineService::class);
                    
                    $sizeArray = explode('x', $data['size']);
                    $result = $service->generateThumbnail(
                        $record->id, 
                        [(int)$sizeArray[0], (int)$sizeArray[1]], 
                        (int)($data['page'] ?? 0)
                    );
                    
                    if ($result['success']) {
                        Notification::make()
                            ->title('Thumbnail erfolgreich generiert')
                            ->body(sprintf('Thumbnail-URL: %s', $result['thumbnail_url']))
                            ->success()
                            ->send();
                    } else {
                        Notification::make()
                            ->title('Thumbnail-Generierung fehlgeschlagen')
                            ->body($result['error'] ?? 'Unbekannter Fehler')
                            ->danger()
                            ->send();
                    }
                }),

            Action::make('reprocessDocument')
                ->label('Neu verarbeiten')
                ->icon('heroicon-o-arrow-path')
                ->requiresConfirmation()
                ->visible(function (): bool {
                    $user = auth()->user();

                    if (! $user) {
                        return false;
                    }

                    if (method_exists($user, 'canManageContent')) {
                        return $user->canManageContent();
                    }

                    return true;
                })
                ->action(function (): void {
                    $record = $this->getRecord();
                    $service = app(KraiEngineService::class);

                    $result = $service->reprocessDocument($record->id);
                    
                    if ($result['success']) {
                        Notification::make()
                            ->title('Dokument neu in Verarbeitung')
                            ->body($result['message'] ?? 'Das Dokument wurde erneut zur Verarbeitung eingereiht.')
                            ->success()
                            ->send();
                    } else {
                        Notification::make()
                            ->title('Reprocessing fehlgeschlagen')
                            ->body($result['error'] ?? 'Das Dokument konnte nicht erneut zur Verarbeitung eingereiht werden.')
                            ->danger()
                            ->send();
                    }
                }),
            DeleteAction::make(),
        ];
    }
}

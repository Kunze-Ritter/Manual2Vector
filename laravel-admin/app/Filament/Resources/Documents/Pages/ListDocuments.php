<?php

namespace App\Filament\Resources\Documents\Pages;

use App\Filament\Resources\Documents\DocumentResource;
use App\Services\KraiEngineService;
use Filament\Actions\Action;
use Filament\Forms\Components\CheckboxList;
use Filament\Forms\Components\FileUpload;
use Filament\Forms\Components\Get;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\ListRecords;
use Illuminate\Support\Facades\Http;

class ListDocuments extends ListRecords
{
    protected static string $resource = DocumentResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Action::make('uploadDocument')
                ->label('Dokument hochladen')
                ->icon('heroicon-o-arrow-up-on-square')
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
                    FileUpload::make('file')
                        ->label('PDF-Datei')
                        ->acceptedFileTypes(['application/pdf'])
                        ->required(),
                    Select::make('document_type')
                        ->label('Dokumenttyp')
                        ->options([
                            'service_manual' => 'Service Manual',
                            'parts_catalog' => 'Parts Catalog',
                            'technical_bulletin' => 'Technical Bulletin',
                            'cpmd_database' => 'CPMD Database',
                            'user_manual' => 'User Manual',
                            'installation_guide' => 'Installation Guide',
                            'troubleshooting_guide' => 'Troubleshooting Guide',
                        ])
                        ->required()
                        ->default('service_manual'),
                    TextInput::make('language')
                        ->label('Sprache')
                        ->maxLength(10)
                        ->default('en'),
                    CheckboxList::make('stages')
                        ->label('Stages zur Verarbeitung (optional)')
                        ->options(collect(config('krai.stages'))->mapWithKeys(fn($stage, $key) => [$key => $stage['label']]))
                        ->columns(3)
                        ->helperText('Leer lassen für vollständige Verarbeitung (alle Stages)')
                        ->default(null),
                    Toggle::make('stop_on_error')
                        ->label('Bei Fehler stoppen')
                        ->default(true)
                        ->helperText('Verarbeitung bei erstem Fehler abbrechen')
                        ->visible(fn(Get $get) => !empty($get('stages'))),
                ])
                ->action(function (array $data): void {
                    $file = $data['file'];
                    $service = app(KraiEngineService::class);
                    $user = auth()->user();
                    
                    // Upload document using service
                    $uploadResult = $service->uploadDocument(
                        $file,
                        $data['document_type'],
                        $data['language'] ?? 'en',
                        $user
                    );
                    
                    if (!$uploadResult['success']) {
                        Notification::make()
                            ->title('Upload fehlgeschlagen')
                            ->body($uploadResult['error'] ?? 'Der Upload konnte nicht durchgeführt werden.')
                            ->danger()
                            ->send();
                        return;
                    }
                    
                    $documentId = $uploadResult['document_id'];
                    
                    if (!$documentId) {
                        Notification::make()
                            ->title('Upload fehlgeschlagen')
                            ->body('Dokument-ID konnte nicht ermittelt werden.')
                            ->danger()
                            ->send();
                        return;
                    }
                    
                    // If custom stages selected, process them
                    if (!empty($data['stages'])) {
                        $stageResult = $service->processMultipleStages(
                            $documentId,
                            $data['stages'],
                            $data['stop_on_error'] ?? true,
                            $user
                        );
                        
                        if ($stageResult['success']) {
                            Notification::make()
                                ->title('Dokument hochgeladen und verarbeitet')
                                ->body(sprintf('Upload erfolgreich. %d von %d Stages abgeschlossen.', $stageResult['successful'], $stageResult['total_stages']))
                                ->success()
                                ->send();
                        } else {
                            Notification::make()
                                ->title('Dokument hochgeladen, Verarbeitung teilweise fehlgeschlagen')
                                ->body(sprintf('%d erfolgreich, %d fehlgeschlagen', $stageResult['successful'], $stageResult['failed']))
                                ->warning()
                                ->send();
                        }
                    } else {
                        // Default: full background processing (existing behavior)
                        Notification::make()
                            ->title('Dokumenten-Upload gestartet')
                            ->body('Das Dokument wurde hochgeladen und wird im Hintergrund verarbeitet.')
                            ->success()
                            ->send();
                    }
                    
                    // Refresh the documents table to show the new document
                    $this->resetTable();
                }),
            // Kein Create-Button, Upload läuft (später) über eigenen Flow
        ];
    }
}

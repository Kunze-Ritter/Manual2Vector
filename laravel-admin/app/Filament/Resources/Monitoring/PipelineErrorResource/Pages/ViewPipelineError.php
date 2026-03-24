<?php

namespace App\Filament\Resources\Monitoring\PipelineErrorResource\Pages;

use App\Filament\Resources\Monitoring\PipelineErrorResource;
use Filament\Actions;
use Filament\Forms\Components\Textarea;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\ViewRecord;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;
use Illuminate\Support\Facades\Log;

class ViewPipelineError extends ViewRecord
{
    protected static string $resource = PipelineErrorResource::class;

    public function infolist(Schema $schema): Schema
    {
        return $schema->components([
            Section::make('Fehlermeldung')
                ->schema([
                    TextInput::make('error_message')
                        ->label('')
                        ->disabled()
                        ->columnSpanFull(),
                ])
                ->collapsible(false),

            Section::make('Fehlerinformationen')
                ->schema([
                    Grid::make(3)
                        ->schema([
                            TextInput::make('document.id')
                                ->label('Dokument-ID')
                                ->disabled()
                                ->copyable(),

                            TextInput::make('stage_name')
                                ->label('Stage')
                                ->disabled(),

                            TextInput::make('error_type')
                                ->label('Fehlertyp')
                                ->disabled(),

                            TextInput::make('created_at')
                                ->label('Zeitstempel')
                                ->disabled(),

                            TextInput::make('retry_count')
                                ->label('Retry-Anzahl')
                                ->disabled()
                                ->formatStateUsing(fn ($record) => "{$record->retry_count}/{$record->max_retries}"),

                            TextInput::make('error_id')
                                ->label('Error-ID')
                                ->disabled()
                                ->copyable(),

                            TextInput::make('severity')
                                ->label('Schweregrad')
                                ->disabled(),

                            TextInput::make('status')
                                ->label('Status')
                                ->disabled()
                                ->formatStateUsing(fn ($state) => ucfirst($state)),

                            TextInput::make('resolved_at')
                                ->label('Gelöst am')
                                ->disabled()
                                ->visible(fn ($record) => $record->resolved_at !== null),
                        ]),
                ]),

            Section::make('Retry-Historie')
                ->schema([
                    \Filament\Forms\Components\ViewField::make('stage_status')
                        ->label('')
                        ->view('filament.forms.components.stage-status-retry-history')
                        ->columnSpanFull(),
                ])
                ->collapsible()
                ->visible(fn ($record) => $record->stage_status && is_array($record->stage_status) && count($record->stage_status) > 0),

            Section::make('Stack Trace')
                ->schema([
                    \Filament\Forms\Components\ViewField::make('stack_trace')
                        ->label('')
                        ->view('filament.forms.components.stack-trace-display')
                        ->columnSpanFull(),
                ])
                ->collapsible()
                ->collapsed()
                ->visible(fn ($record) => $record->stack_trace !== null),

            Section::make('Context')
                ->schema([
                    \Filament\Forms\Components\ViewField::make('context')
                        ->label('')
                        ->view('filament.forms.components.json-display')
                        ->columnSpanFull(),
                ])
                ->collapsible()
                ->collapsed()
                ->visible(fn ($record) => $record->context !== null),

            Section::make('Lösungsnotizen')
                ->schema([
                    TextInput::make('resolution_notes')
                        ->label('')
                        ->disabled()
                        ->columnSpanFull(),

                    TextInput::make('resolvedBy.name')
                        ->label('Gelöst von')
                        ->disabled(),
                ])
                ->visible(fn ($record) => $record->status === 'resolved' && $record->resolution_notes !== null),
        ]);
    }

    protected function getHeaderActions(): array
    {
        return [
            Actions\Action::make('retryStage')
                ->label('Stage erneut versuchen')
                ->icon('heroicon-o-arrow-path')
                ->color('warning')
                ->visible(fn () => $this->record->status !== 'resolved')
                ->disabled(fn (): bool => $this->getRetryDisabledReason() !== null)
                ->tooltip(fn (): ?string => $this->getRetryDisabledReason())
                ->requiresConfirmation()
                ->modalHeading('Stage erneut versuchen')
                ->modalDescription('Möchten Sie diese Stage wirklich erneut versuchen?')
                ->action(function () {
                    try {
                        $result = PipelineErrorResource::getBackendApiService()->retryStage(
                            $this->record->document_id,
                            $this->record->stage_name,
                        );

                        if ($result['success'] === true) {
                            Notification::make()
                                ->title('Stage wird erneut verarbeitet')
                                ->body("Stage '{$this->record->stage_name}' wird für Dokument {$this->record->document_id} erneut verarbeitet.")
                                ->success()
                                ->send();

                            return redirect()->route('filament.kradmin.resources.monitoring.pipeline-errors.view', $this->record);
                        }

                        Notification::make()
                            ->title('Retry fehlgeschlagen')
                            ->body((string) ($result['error'] ?? 'Unbekannter Fehler beim Retry-Versuch.'))
                            ->danger()
                            ->send();
                    } catch (\Exception $e) {
                        Log::error('Pipeline retry action failed on view page', [
                            'error_id' => $this->record->error_id,
                            'document_id' => $this->record->document_id,
                            'stage_name' => $this->record->stage_name,
                            'exception' => $e->getMessage(),
                        ]);

                        Notification::make()
                            ->title('Retry fehlgeschlagen')
                            ->body('Ein unerwarteter Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.')
                            ->danger()
                            ->send();
                    }
                }),

            Actions\Action::make('markResolved')
                ->label('Als gelöst markieren')
                ->icon('heroicon-o-check-circle')
                ->color('success')
                ->visible(fn () => $this->record->status !== 'resolved')
                ->form([
                    Textarea::make('resolution_notes')
                        ->label('Lösungsnotizen')
                        ->required()
                        ->maxLength(1000)
                        ->rows(4),
                ])
                ->action(function (array $data) {
                    $this->record->update([
                        'status' => 'resolved',
                        'resolved_at' => now(),
                        'resolved_by' => auth()->id(),
                        'resolution_notes' => $data['resolution_notes'],
                    ]);

                    try {
                        $result = PipelineErrorResource::getBackendApiService()->markErrorResolved(
                            $this->record->error_id,
                            auth()->id(),
                            $data['resolution_notes'],
                        );

                        if ($result['success'] === true) {
                            Notification::make()
                                ->title('Fehler als gelöst markiert')
                                ->body('Fehler wurde lokal und im Backend als gelöst markiert.')
                                ->success()
                                ->send();
                        } else {
                            Log::warning('Backend sync failed for resolved error on view page', [
                                'error_id' => $this->record->error_id,
                                'error' => $result['error'] ?? 'Unknown error',
                            ]);

                            Notification::make()
                                ->title('Fehler lokal markiert')
                                ->body('Fehler lokal markiert, aber Backend-Synchronisation fehlgeschlagen: '.(string) ($result['error'] ?? 'Unbekannter Fehler'))
                                ->warning()
                                ->send();
                        }
                    } catch (\Exception $e) {
                        Log::error('Exception during backend sync for resolved error on view page', [
                            'error_id' => $this->record->error_id,
                            'exception' => $e->getMessage(),
                        ]);

                        Notification::make()
                            ->title('Fehler lokal markiert')
                            ->body('Fehler lokal markiert, aber Backend-Synchronisation fehlgeschlagen.')
                            ->warning()
                            ->send();
                    }

                    return redirect()->route('filament.kradmin.resources.monitoring.pipeline-errors.view', $this->record);
                }),

            Actions\Action::make('copyErrorId')
                ->label('Error-ID kopieren')
                ->icon('heroicon-o-clipboard-document')
                ->action(function () {
                    Notification::make()
                        ->title('Error-ID kopiert')
                        ->body($this->record->error_id)
                        ->success()
                        ->send();
                })
                ->extraAttributes(fn () => [
                    'x-on:click' => 'navigator.clipboard.writeText("'.e($this->record->error_id).'")',
                ]),

            Actions\Action::make('viewDocument')
                ->label('Dokument anzeigen')
                ->icon('heroicon-o-document-text')
                ->url(fn () => $this->record->document_id
                    ? route('filament.kradmin.resources.documents.edit', $this->record->document_id)
                    : null
                )
                ->visible(fn () => $this->record->document_id !== null),
        ];
    }

    private function getRetryDisabledReason(): ?string
    {
        $service = PipelineErrorResource::getBackendApiService();

        if (! $service->validateConfiguration()) {
            return 'Backend-Konfiguration für Retry ist unvollständig.';
        }

        $normalizedStage = $service->normalizeRetryStageName($this->record->stage_name);

        if ($normalizedStage === null) {
            return "Für die Stage '{$this->record->stage_name}' ist derzeit kein Admin-Retry verfügbar.";
        }

        $stageStatus = $this->record->document?->stage_status;
        $documentStage = is_array($stageStatus) ? ($stageStatus[$normalizedStage] ?? null) : null;
        $documentStageStatus = is_array($documentStage) ? ($documentStage['status'] ?? null) : null;

        if ($documentStageStatus !== 'failed') {
            return "Retry ist nur verfügbar, wenn die Dokument-Stage '{$normalizedStage}' im Status 'failed' ist.";
        }

        return null;
    }
}

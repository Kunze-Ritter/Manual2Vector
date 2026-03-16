<?php

namespace App\Filament\Resources\Monitoring\PipelineErrorResource\Pages;

use App\Filament\Resources\Monitoring\PipelineErrorResource;
use Filament\Actions;
use Filament\Forms\Components\Section;
use Filament\Forms\Components\TextInput;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\ViewRecord;
use Filament\Schemas\Components\Grid;
use Filament\Schemas\Schema;

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
                                ->copyable()
                                ->color('primary'),

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
                ->requiresConfirmation()
                ->modalHeading('Stage erneut versuchen')
                ->modalDescription('Möchten Sie diese Stage wirklich erneut versuchen?')
                ->action(function () {
                    Notification::make()
                        ->title('Retry-Funktion')
                        ->body('Backend-API-Integration wird in einer späteren Phase implementiert.')
                        ->warning()
                        ->send();
                }),

            Actions\Action::make('markResolved')
                ->label('Als gelöst markieren')
                ->icon('heroicon-o-check-circle')
                ->color('success')
                ->visible(fn () => $this->record->status !== 'resolved')
                ->form([
                    \Filament\Forms\Components\Textarea::make('resolution_notes')
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

                    Notification::make()
                        ->title('Fehler als gelöst markiert')
                        ->success()
                        ->send();

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
}

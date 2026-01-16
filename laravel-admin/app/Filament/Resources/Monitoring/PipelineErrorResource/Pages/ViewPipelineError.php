<?php

namespace App\Filament\Resources\Monitoring\PipelineErrorResource\Pages;

use App\Filament\Resources\Monitoring\PipelineErrorResource;
use Filament\Actions;
use Filament\Infolists\Components\Grid;
use Filament\Infolists\Components\Section;
use Filament\Infolists\Components\TextEntry;
use Filament\Infolists\Infolist;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\ViewRecord;

class ViewPipelineError extends ViewRecord
{
    protected static string $resource = PipelineErrorResource::class;

    protected static string $view = 'filament.resources.monitoring.pages.view-pipeline-error';

    public function infolist(Infolist $infolist): Infolist
    {
        return $infolist
            ->schema([
                Section::make('Fehlermeldung')
                    ->schema([
                        TextEntry::make('error_message')
                            ->label('')
                            ->color('danger')
                            ->size(TextEntry\TextEntrySize::Large)
                            ->weight('bold')
                            ->columnSpanFull(),
                    ])
                    ->collapsible(false),

                Section::make('Fehlerinformationen')
                    ->schema([
                        Grid::make(3)
                            ->schema([
                                TextEntry::make('document.id')
                                    ->label('Dokument-ID')
                                    ->copyable()
                                    ->copyMessage('Dokument-ID kopiert')
                                    ->url(fn ($record) => $record->document_id 
                                        ? route('filament.kradmin.resources.documents.documents.edit', $record->document_id)
                                        : null
                                    )
                                    ->color('primary'),

                                TextEntry::make('stage_name')
                                    ->label('Stage')
                                    ->badge(),

                                TextEntry::make('error_type')
                                    ->label('Fehlertyp')
                                    ->badge()
                                    ->color(fn ($record) => match($record->severity ?? 'medium') {
                                        'critical', 'high' => 'danger',
                                        'medium' => 'warning',
                                        'low' => 'info',
                                        default => 'gray',
                                    }),

                                TextEntry::make('created_at')
                                    ->label('Zeitstempel')
                                    ->dateTime('Y-m-d H:i:s'),

                                TextEntry::make('retry_count')
                                    ->label('Retry-Anzahl')
                                    ->formatStateUsing(fn ($record) => "{$record->retry_count}/{$record->max_retries}"),

                                TextEntry::make('error_id')
                                    ->label('Error-ID')
                                    ->copyable()
                                    ->copyMessage('Error-ID kopiert'),

                                TextEntry::make('severity')
                                    ->label('Schweregrad')
                                    ->badge()
                                    ->color(fn ($state) => match($state) {
                                        'critical', 'high' => 'danger',
                                        'medium' => 'warning',
                                        'low' => 'info',
                                        default => 'gray',
                                    }),

                                TextEntry::make('status')
                                    ->label('Status')
                                    ->badge()
                                    ->color(fn ($state) => PipelineErrorResource::getStatusBadgeColor($state))
                                    ->formatStateUsing(fn ($state) => ucfirst($state)),

                                TextEntry::make('resolved_at')
                                    ->label('Gelöst am')
                                    ->dateTime('Y-m-d H:i:s')
                                    ->placeholder('Nicht gelöst')
                                    ->visible(fn ($record) => $record->resolved_at !== null),
                            ]),
                    ]),

                Section::make('Retry-Historie')
                    ->schema([
                        TextEntry::make('stage_status')
                            ->label('')
                            ->formatStateUsing(function ($state, $record) {
                                if (!$state || !is_array($state)) {
                                    return 'Keine Retry-Historie verfügbar';
                                }

                                $html = '<div class="space-y-2">';
                                foreach ($state as $index => $retry) {
                                    $timestamp = e($retry['timestamp'] ?? 'N/A');
                                    $status = e($retry['status'] ?? 'unknown');
                                    $message = e($retry['message'] ?? 'Keine Nachricht');
                                    
                                    $icon = match($retry['status'] ?? 'unknown') {
                                        'success' => '✅',
                                        'failed' => '❌',
                                        'retrying' => '🔄',
                                        default => '⚠️',
                                    };

                                    $color = match($retry['status'] ?? 'unknown') {
                                        'success' => 'text-green-600',
                                        'failed' => 'text-red-600',
                                        'retrying' => 'text-yellow-600',
                                        default => 'text-gray-600',
                                    };

                                    $html .= "<div class='flex items-start gap-2 p-2 rounded bg-gray-50 dark:bg-gray-800'>";
                                    $html .= "<span class='text-lg'>{$icon}</span>";
                                    $html .= "<div class='flex-1'>";
                                    $html .= "<div class='font-semibold {$color}>" . ucfirst($status) . "</div>";
                                    $html .= "<div class='text-sm text-gray-600 dark:text-gray-400'>{$timestamp}</div>";
                                    $html .= "<div class='text-sm mt-1'>{$message}</div>";
                                    $html .= "</div>";
                                    $html .= "</div>";
                                }
                                $html .= '</div>';

                                return $html;
                            })
                            ->html()
                            ->columnSpanFull(),
                    ])
                    ->collapsible()
                    ->visible(fn ($record) => $record->stage_status && is_array($record->stage_status) && count($record->stage_status) > 0),

                Section::make('Stack Trace')
                    ->schema([
                        TextEntry::make('stack_trace')
                            ->label('')
                            ->formatStateUsing(fn ($state) => $state ? "<pre class='text-xs overflow-x-auto'><code>" . e($state) . "</code></pre>" : 'Kein Stack Trace verfügbar')
                            ->html()
                            ->columnSpanFull(),
                    ])
                    ->collapsible()
                    ->collapsed()
                    ->visible(fn ($record) => $record->stack_trace !== null),

                Section::make('Context')
                    ->schema([
                        TextEntry::make('context')
                            ->label('')
                            ->formatStateUsing(fn ($state) => $state 
                                ? "<pre class='text-xs overflow-x-auto'><code>" . json_encode($state, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "</code></pre>"
                                : 'Kein Context verfügbar'
                            )
                            ->html()
                            ->columnSpanFull(),
                    ])
                    ->collapsible()
                    ->collapsed()
                    ->visible(fn ($record) => $record->context !== null),

                Section::make('Lösungsnotizen')
                    ->schema([
                        TextEntry::make('resolution_notes')
                            ->label('')
                            ->columnSpanFull(),

                        TextEntry::make('resolvedBy.name')
                            ->label('Gelöst von')
                            ->placeholder('N/A'),
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
                ->extraAttributes([
                    'x-on:click' => 'navigator.clipboard.writeText("' . e($this->record->error_id) . '")',
                ]),

            Actions\Action::make('viewDocument')
                ->label('Dokument anzeigen')
                ->icon('heroicon-o-document-text')
                ->url(fn () => $this->record->document_id 
                    ? route('filament.kradmin.resources.documents.documents.edit', $this->record->document_id)
                    : null
                )
                ->visible(fn () => $this->record->document_id !== null),
        ];
    }
}

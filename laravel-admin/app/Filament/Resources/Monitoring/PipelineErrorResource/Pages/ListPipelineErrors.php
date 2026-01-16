<?php

namespace App\Filament\Resources\Monitoring\PipelineErrorResource\Pages;

use App\Filament\Resources\Monitoring\PipelineErrorResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListPipelineErrors extends ListRecords
{
    protected static string $resource = PipelineErrorResource::class;

    protected static ?string $pollingInterval = '15s';

    protected function getHeaderActions(): array
    {
        return [
            Actions\Action::make('refreshErrors')
                ->label('Aktualisieren')
                ->icon('heroicon-o-arrow-path')
                ->action(fn() => $this->dispatch('$refresh')),
        ];
    }
}

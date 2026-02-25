<?php

namespace App\Filament\Resources\AI\PromptTemplateResource\Pages;

use App\Filament\Resources\AI\PromptTemplateResource;
use Filament\Actions\CreateAction;
use Filament\Resources\Pages\ListRecords;

class ListPromptTemplates extends ListRecords
{
    protected static string $resource = PromptTemplateResource::class;

    protected function getHeaderActions(): array
    {
        return [CreateAction::make()];
    }
}

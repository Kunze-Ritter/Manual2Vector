<?php

namespace App\Filament\Widgets;

use Filament\Widgets\Widget;

class VersionWidget extends Widget
{
    protected string $view = 'filament.widgets.version';

    protected static ?int $sort = -1;

    protected int|string|array $columnSpan = 'full';

    protected function getViewData(): array
    {
        return [
            'version' => 'KRAI v1.0',
        ];
    }
}

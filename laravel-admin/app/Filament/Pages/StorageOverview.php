<?php

namespace App\Filament\Pages;

use BackedEnum;
use Filament\Pages\Page;
use Illuminate\Support\Facades\DB;
use UnitEnum;

class StorageOverview extends Page
{
    protected static ?string $navigationLabel = 'Storage';

    protected static string | UnitEnum | null $navigationGroup = 'Medien';

    protected static string | BackedEnum | null $navigationIcon = 'heroicon-o-photo';

    protected string $storageView = 'filament.pages.storage-overview';

    public int $totalImages = 0;

    public string $totalSize = '0 B';

    public int $documentsWithImages = 0;

    public function mount(): void
    {
        $this->loadStats();
    }

    protected function loadStats(): void
    {
        try {
            $this->totalImages = (int) DB::table('krai_content.images')->count();

            $totalBytes = (int) DB::table('krai_content.images')->sum('file_size');
            $this->totalSize = $this->formatSize($totalBytes);

            $this->documentsWithImages = (int) DB::table('krai_content.images')
                ->distinct('document_id')
                ->count('document_id');
        } catch (\Throwable $e) {
            // Fallback to zeros if DB query fails
            $this->totalImages = 0;
            $this->totalSize = '0 B';
            $this->documentsWithImages = 0;
        }
    }

    protected function formatSize(int $bytes): string
    {
        if ($bytes <= 0) {
            return '0 B';
        }

        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        $power = (int) floor(log($bytes, 1024));
        $power = max(0, min($power, count($units) - 1));

        $value = $bytes / (1024 ** $power);

        return number_format($value, 2) . ' ' . $units[$power];
    }

    public function getView(): string
    {
        return $this->storageView;
    }

    protected function getViewData(): array
    {
        return [
            'totalImages' => $this->totalImages,
            'totalSize' => $this->totalSize,
            'documentsWithImages' => $this->documentsWithImages,
        ];
    }
}

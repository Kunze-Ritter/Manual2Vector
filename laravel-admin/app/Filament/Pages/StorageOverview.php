<?php

namespace App\Filament\Pages;

use App\Models\Document;
use App\Services\ImageService;
use BackedEnum;
use Filament\Pages\Page;
use Filament\Actions\Concerns\InteractsWithActions;
use Filament\Actions\Contracts\HasActions;
use Filament\Actions\Action;
use Illuminate\Support\Arr;
use Illuminate\Support\Collection;
use Illuminate\Support\Facades\Notification;
use UnitEnum;

class StorageOverview extends Page implements HasActions
{
    use InteractsWithActions;

    protected static ?string $navigationLabel = 'Bilder & Storage';

    protected static string | UnitEnum | null $navigationGroup = 'Content';

    protected static string | BackedEnum | null $navigationIcon = 'heroicon-o-photo';

    protected static ?int $navigationSort = 3;

    public string $pollingInterval;

    public bool $imagesLoaded = false;

    public bool $isLoading = false;

    public ?string $filterDocument = null;

    public ?string $filterDateFrom = null;

    public ?string $filterDateTo = null;

    public ?int $filterFileSizeMin = null;

    public ?int $filterFileSizeMax = null;

    public string $filterSearch = '';

    public int $page = 1;

    public int $pageSize;

    public string $sortBy = 'created_at';

    public string $sortOrder = 'desc';

    public array $selectedImages = [];

    public string $viewMode = 'grid';

    public array $images = [];

    public int $total = 0;

    public int $totalPages = 0;

    public array $stats = [];

    protected $queryString = [
        'filterDocument' => ['except' => null],
        'filterDateFrom' => ['except' => null],
        'filterDateTo' => ['except' => null],
        'filterFileSizeMin' => ['except' => null],
        'filterFileSizeMax' => ['except' => null],
        'filterSearch' => ['except' => ''],
        'page' => ['except' => 1],
        'pageSize' => ['except' => null],
        'sortBy' => ['except' => 'created_at'],
        'sortOrder' => ['except' => 'desc'],
        'viewMode' => ['except' => 'grid'],
    ];

    public function mount(): void
    {
        $this->pollingInterval = config('krai.monitoring.polling_intervals.images', '30s');
        $this->pageSize = config('krai.images.default_page_size', 24);
        $this->loadStats();
    }

    #[\Livewire\Attributes\On('refresh-images')]
    public function loadAll(): void
    {
        $this->loadImages();
        $this->loadStats();
    }

    public function loadImages(bool $append = false): void
    {
        if ($this->isLoading) {
            return;
        }
        $this->isLoading = true;

        $service = app(ImageService::class);
        $filters = [
            'document_id' => $this->filterDocument,
            'date_from' => $this->filterDateFrom,
            'date_to' => $this->filterDateTo,
            'file_size_min' => $this->filterFileSizeMin ? $this->filterFileSizeMin * 1024 * 1024 : null,
            'file_size_max' => $this->filterFileSizeMax ? $this->filterFileSizeMax * 1024 * 1024 : null,
            'search' => $this->filterSearch,
        ];

        $filters = array_filter($filters, static fn ($value) => $value !== null && $value !== '');

        $response = $service->listImages($filters, $this->page, $this->pageSize, $this->sortBy, $this->sortOrder);
        $payload = $response['data'] ?? [];
        if ($response['success'] && isset($payload['images'])) {
            $this->images = $append ? array_merge($this->images, $payload['images']) : $payload['images'];
            $this->total = (int) ($payload['total'] ?? 0);
            $this->totalPages = (int) ($payload['total_pages'] ?? 0);
            $this->imagesLoaded = true;
        } else {
            if (!$append) {
                $this->images = [];
                $this->total = 0;
                $this->totalPages = 0;
            }
        }

        $this->isLoading = false;
    }

    public function loadStats(): void
    {
        $service = app(ImageService::class);
        $response = $service->getImageStats();
        $this->stats = $response['data'] ?? [];
    }

    public function getDocuments(): Collection
    {
        return Document::query()
            ->orderBy('filename')
            ->get(['id', 'filename']);
    }

    public function applyFilters(): void
    {
        $this->page = 1;
        $this->images = [];
        $this->loadImages();
    }

    public function resetFilters(): void
    {
        $this->filterDocument = null;
        $this->filterDateFrom = null;
        $this->filterDateTo = null;
        $this->filterFileSizeMin = null;
        $this->filterFileSizeMax = null;
        $this->filterSearch = '';
        $this->page = 1;
        $this->images = [];
        $this->loadImages();
    }

    public function changePage(int $page): void
    {
        if ($page < 1 || ($this->totalPages > 0 && $page > $this->totalPages)) {
            return;
        }
        $this->page = $page;
        $this->loadImages();
    }

    public function loadMore(): void
    {
        if ($this->page >= $this->totalPages || $this->isLoading) {
            return;
        }

        $this->page++;
        $this->loadImages(true);
    }

    public function updatedPageSize(): void
    {
        $max = config('krai.images.max_page_size', 96);
        if ($this->pageSize > $max) {
            $this->pageSize = $max;
        }
        $this->page = 1;
        $this->loadImages();
    }

    public function sortBy(string $column): void
    {
        if ($this->sortBy === $column) {
            $this->sortOrder = $this->sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
            $this->sortBy = $column;
            $this->sortOrder = 'asc';
        }
        $this->loadImages();
    }

    public function toggleImageSelection(string $imageId): void
    {
        if (in_array($imageId, $this->selectedImages, true)) {
            $this->selectedImages = array_values(array_diff($this->selectedImages, [$imageId]));
        } else {
            $this->selectedImages[] = $imageId;
        }
    }

    public function selectAll(): void
    {
        $this->selectedImages = Arr::pluck($this->images, 'id');
    }

    public function deselectAll(): void
    {
        $this->selectedImages = [];
    }

    public function deleteSelectedAction(): Action
    {
        return Action::make('deleteSelected')
            ->requiresConfirmation()
            ->modalHeading('Ausgewählte Bilder löschen')
            ->modalDescription('Bist du sicher, dass du die ausgewählten Bilder löschen möchtest?')
            ->modalWidth('3xl')
            ->action(function () {
                $this->deleteSelected();
            });
    }

    public function deleteSelected(): void
    {
        if (empty($this->selectedImages)) {
            Notification::make()
                ->title('Keine Bilder ausgewählt')
                ->danger()
                ->send();
            return;
        }

        $service = app(ImageService::class);
        $summary = $service->bulkDeleteImages($this->selectedImages, true);
        $this->deselectAll();
        $this->loadImages();
        $this->loadStats();

        $message = "Gelöscht: {$summary['success']} | Fehlgeschlagen: {$summary['failed']}";
        Notification::make()
            ->title('Löschvorgang abgeschlossen')
            ->body($message)
            ->success()
            ->send();
    }

    public function downloadSelected(): ?\Symfony\Component\HttpFoundation\StreamedResponse
    {
        if (empty($this->selectedImages)) {
            Notification::make()
                ->title('Keine Bilder ausgewählt')
                ->danger()
                ->send();
            return null;
        }

        $limit = config('krai.images.bulk_download_limit', 100);
        if (count($this->selectedImages) > $limit) {
            Notification::make()
                ->title("Maximal {$limit} Bilder pro ZIP")
                ->danger()
                ->send();
            return null;
        }

        $service = app(ImageService::class);
        $zipPath = $service->createBulkDownloadZip($this->selectedImages);
        if (!$zipPath) {
            Notification::make()
                ->title('ZIP konnte nicht erstellt werden')
                ->danger()
                ->send();
            return null;
        }

        $this->deselectAll();

        return response()->download($zipPath, 'images.zip')->deleteFileAfterSend(true);
    }

    public function getActions(): array
    {
        return [
            $this->deleteSelectedAction(),
            Action::make('downloadSelected')
                ->label('Ausgewählte herunterladen')
                ->action(fn () => $this->downloadSelected()),
        ];
    }

    public function getViewData(): array
    {
        return [
            'images' => $this->images,
            'stats' => $this->stats,
            'documents' => $this->getDocuments(),
            'filterDocument' => $this->filterDocument,
            'filterDateFrom' => $this->filterDateFrom,
            'filterDateTo' => $this->filterDateTo,
            'filterFileSizeMin' => $this->filterFileSizeMin,
            'filterFileSizeMax' => $this->filterFileSizeMax,
            'filterSearch' => $this->filterSearch,
            'page' => $this->page,
            'pageSize' => $this->pageSize,
            'sortBy' => $this->sortBy,
            'sortOrder' => $this->sortOrder,
            'selectedImages' => $this->selectedImages,
            'viewMode' => $this->viewMode,
            'total' => $this->total,
            'totalPages' => $this->totalPages,
            'pollingInterval' => $this->pollingInterval,
        ];
    }
}

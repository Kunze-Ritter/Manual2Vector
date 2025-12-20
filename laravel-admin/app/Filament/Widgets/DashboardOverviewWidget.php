<?php

namespace App\Filament\Widgets;

use App\Services\MonitoringService;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class DashboardOverviewWidget extends BaseWidget
{
    protected static ?int $sort = 1;

    protected function getPollingInterval(): ?string
    {
        return config('krai.monitoring.polling_intervals.dashboard', '30s');
    }

    protected function getStats(): array
    {
        $monitoringService = app(MonitoringService::class);
        $batch = $monitoringService->getDashboardBatch();
        $result = $batch['dashboard'] ?? $monitoringService->getDashboardOverview();

        if (!$result['success']) {
            return $this->getFallbackStats($result['error']);
        }

        $data = $result['data'] ?? [];

        return [
            $this->getDocumentsStat($data),
            $this->getProductsStat($data),
            $this->getQueueStat($data),
            $this->getMediaStat($data),
        ];
    }

    private function getDocumentsStat(array $data): Stat
    {
        $documents = $data['documents'] ?? [];
        $total = $documents['total'] ?? 0;
        $byStatus = $documents['by_status'] ?? [];

        $pending = $byStatus['pending'] ?? 0;
        $processing = $byStatus['processing'] ?? 0;
        $completed = $byStatus['completed'] ?? 0;
        $failed = $byStatus['failed'] ?? 0;

        $description = sprintf(
            'Pending: %d | Processing: %d | Completed: %d | Failed: %d',
            $pending,
            $processing,
            $completed,
            $failed
        );

        $color = 'success';
        if ($failed > 0) {
            $color = 'warning';
        }
        if ($failed > $completed / 10) {
            $color = 'danger';
        }

        return Stat::make('Documents', number_format($total))
            ->description($description)
            ->descriptionIcon('heroicon-o-document-text')
            ->color($color)
            ->chart([$pending, $processing, $completed, $failed]);
    }

    private function getProductsStat(array $data): Stat
    {
        $products = $data['products'] ?? [];
        $total = $products['total'] ?? 0;
        $active = $products['active'] ?? 0;
        $discontinued = $products['discontinued'] ?? 0;

        $description = sprintf(
            'Active: %d | Discontinued: %d',
            $active,
            $discontinued
        );

        return Stat::make('Products', number_format($total))
            ->description($description)
            ->descriptionIcon('heroicon-o-cube')
            ->color('info')
            ->chart([$active, $discontinued]);
    }

    private function getQueueStat(array $data): Stat
    {
        $queue = $data['queue'] ?? [];
        $total = $queue['total'] ?? 0;
        $byStatus = $queue['by_status'] ?? [];

        $pending = $byStatus['pending'] ?? 0;
        $processing = $byStatus['processing'] ?? 0;
        $completed = $byStatus['completed'] ?? 0;
        $failed = $byStatus['failed'] ?? 0;

        $description = sprintf(
            'Pending: %d | Processing: %d | Completed: %d | Failed: %d',
            $pending,
            $processing,
            $completed,
            $failed
        );

        $color = 'success';
        if ($pending > 100) {
            $color = 'warning';
        }
        if ($pending > 500) {
            $color = 'danger';
        }

        return Stat::make('Queue', number_format($total))
            ->description($description)
            ->descriptionIcon('heroicon-o-queue-list')
            ->color($color)
            ->chart([$pending, $processing, $completed, $failed]);
    }

    private function getMediaStat(array $data): Stat
    {
        $media = $data['media'] ?? [];
        $images = $media['images'] ?? 0;
        $videos = $media['videos'] ?? 0;
        $total = $images + $videos;

        $description = sprintf(
            'Images: %d | Videos: %d',
            $images,
            $videos
        );

        return Stat::make('Media', number_format($total))
            ->description($description)
            ->descriptionIcon('heroicon-o-photo')
            ->color('success')
            ->chart([$images, $videos]);
    }

    private function getFallbackStats(?string $error): array
    {
        return [
            Stat::make('Documents', 'N/A')
                ->description($error ?? 'Unable to fetch data')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
            Stat::make('Products', 'N/A')
                ->description('Offline')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
            Stat::make('Queue', 'N/A')
                ->description('Offline')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
            Stat::make('Media', 'N/A')
                ->description('Offline')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
        ];
    }
}

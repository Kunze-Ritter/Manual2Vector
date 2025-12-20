<?php

namespace App\Filament\Pages;

use App\Services\MonitoringService;
use Carbon\Carbon;
use Filament\Pages\Page;

class QueueMonitoringPage extends Page
{
    protected static ?string $navigationLabel = 'Warteschlangen';

    protected static \UnitEnum|string|null $navigationGroup = 'Monitoring';

    protected static \BackedEnum|string|null $navigationIcon = 'heroicon-o-queue-list';

    protected static ?int $navigationSort = 3;

    public string $statusFilter = 'all';

    protected static ?string $pollingInterval = null;

    public static function getNavigationBadge(): ?string
    {
        try {
            $response = app(MonitoringService::class)->getQueueStatusBadge();

            if ($response['success'] ?? false) {
                $data = is_array($response['data'] ?? null) ? $response['data'] : [];
                $metrics = is_array($data['queue_metrics'] ?? null) ? $data['queue_metrics'] : $data;
                $pending = (int) ($metrics['pending_count'] ?? 0);

                return $pending > 0 ? (string) $pending : null;
            }
        } catch (\Throwable $e) {
            // Silent fail
        }

        return null;
    }

    public static function getNavigationBadgeColor(): ?string
    {
        return 'warning';
    }

    public function getQueueData(): array
    {
        try {
            $response = app(MonitoringService::class)->getQueueStatus();

            if (!($response['success'] ?? false)) {
                return [
                    'success' => false,
                    'error' => $response['error'] ?? 'Unbekannter Fehler',
                    'queue_metrics' => [],
                    'queue_items' => [],
                ];
            }

            $data = is_array($response['data'] ?? null) ? $response['data'] : [];
            $metrics = is_array($data['queue_metrics'] ?? null) ? $data['queue_metrics'] : [];
            $items = is_array($data['queue_items'] ?? null) ? $data['queue_items'] : [];

            return [
                'success' => true,
                'error' => null,
                'queue_metrics' => $metrics ?: $data,
                'queue_items' => $items,
            ];
        } catch (\Throwable $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
                'queue_metrics' => [],
                'queue_items' => [],
            ];
        }
    }

    public function getFilteredItems(array $items): array
    {
        $status = strtolower($this->statusFilter);

        if ($status === 'all') {
            return $items;
        }

        return array_values(array_filter($items, function ($item) use ($status) {
            return strtolower($item['status'] ?? '') === $status;
        }));
    }

    public function getStatusBadgeColor(string $status): string
    {
        return match (strtolower($status)) {
            'pending' => 'secondary',
            'processing' => 'info',
            'completed' => 'success',
            'failed' => 'danger',
            default => 'gray',
        };
    }

    public function formatDuration(?string $startedAt, ?string $completedAt): string
    {
        if (empty($startedAt)) {
            return '—';
        }

        try {
            $start = Carbon::parse($startedAt);
            $end = $completedAt ? Carbon::parse($completedAt) : Carbon::now();

            return $end->longAbsoluteDiffForHumans($start, 2);
        } catch (\Throwable $e) {
            return '—';
        }
    }

    public function formatRelativeTime(string $timestamp): string
    {
        if (empty($timestamp)) {
            return '—';
        }

        try {
            return Carbon::parse($timestamp)->diffForHumans();
        } catch (\Throwable $e) {
            return '—';
        }
    }

    protected function getViewData(): array
    {
        $queueData = $this->getQueueData();

        $pending = 0;
        if ($queueData['success'] ?? false) {
            $metrics = is_array($queueData['queue_metrics'] ?? null) ? $queueData['queue_metrics'] : [];
            $pending = (int) ($metrics['pending_count'] ?? 0);
        }

        $defaultInterval = (string) config('krai.monitoring.polling_intervals.queue', '20s');
        self::$pollingInterval = $pending > 0 ? $defaultInterval : null;

        return [
            'queueData' => $queueData,
            'statusFilter' => $this->statusFilter,
        ];
    }
}

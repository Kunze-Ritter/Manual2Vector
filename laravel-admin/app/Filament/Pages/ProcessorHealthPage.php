<?php

namespace App\Filament\Pages;

use App\Services\MonitoringService;
use Filament\Pages\Page;

class ProcessorHealthPage extends Page
{
    protected static ?string $navigationLabel = 'Prozessor-Status';

    protected static \UnitEnum|string|null $navigationGroup = 'Monitoring';

    protected static \BackedEnum|string|null $navigationIcon = 'heroicon-o-cpu-chip';

    protected static ?int $navigationSort = 1;

    protected static ?string $pollingInterval = null;

    public static function getNavigationBadge(): ?string
    {
        try {
            $response = app(MonitoringService::class)->getProcessorHealthBadge();

            if ($response['success'] ?? false) {
                $data = is_array($response['data'] ?? null) ? $response['data'] : [];
                $processors = is_array($data['processors'] ?? null) ? $data['processors'] : [];
                $failed = collect($processors)->where('status', 'failed')->count();

                return $failed > 0 ? (string) $failed : null;
            }
        } catch (\Throwable $e) {
            // Silent fail
        }

        return null;
    }

    public static function getNavigationBadgeColor(): ?string
    {
        return 'danger';
    }

    public function getProcessorData(): array
    {
        try {
            $response = app(MonitoringService::class)->getProcessorHealth();

            if (!($response['success'] ?? false)) {
                return [
                    'success' => false,
                    'error' => $response['error'] ?? 'Unbekannter Fehler',
                    'processors' => [],
                ];
            }

            $data = is_array($response['data'] ?? null) ? $response['data'] : [];
            $processors = is_array($data['processors'] ?? null) ? $data['processors'] : [];

            return [
                'success' => true,
                'error' => null,
                'processors' => $processors,
            ];
        } catch (\Throwable $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
                'processors' => [],
            ];
        }
    }

    public function getHealthScoreColor(float $score): string
    {
        if ($score >= 90) {
            return 'text-green-500 stroke-green-500';
        }

        if ($score >= 70) {
            return 'text-yellow-500 stroke-yellow-500';
        }

        return 'text-red-500 stroke-red-500';
    }

    public function getStatusBadgeColor(string $status): string
    {
        return match (strtolower($status)) {
            'running' => 'success',
            'idle' => 'gray',
            'failed' => 'danger',
            'degraded' => 'warning',
            default => 'secondary',
        };
    }

    protected function getViewData(): array
    {
        self::$pollingInterval = (string) config('krai.monitoring.polling_intervals.processor', '30s');

        return [
            'processorData' => $this->getProcessorData(),
        ];
    }
}

<?php

namespace App\Filament\Pages;

use App\Services\MonitoringService;
use Filament\Pages\Page;

class PipelineStatusPage extends Page
{
    protected static ?string $navigationLabel = 'Pipeline-Status';

    protected static \UnitEnum|string|null $navigationGroup = 'Monitoring';

    protected static \BackedEnum|string|null $navigationIcon = 'heroicon-o-arrow-path';

    protected static ?int $navigationSort = 2;

    protected static ?string $pollingInterval = null;

    public function getPipelineData(): array
    {
        try {
            $response = app(MonitoringService::class)->getPipelineStatus();

            if (!($response['success'] ?? false)) {
                return [
                    'success' => false,
                    'error' => $response['error'] ?? 'Unbekannter Fehler',
                    'pipeline_metrics' => [],
                    'stage_metrics' => [],
                    'hardware_status' => [],
                ];
            }

            $data = is_array($response['data'] ?? null) ? $response['data'] : [];
            $pipelineMetrics = is_array($data['pipeline_metrics'] ?? null) ? $data['pipeline_metrics'] : [];
            $stageMetrics = is_array($data['stage_metrics'] ?? null) ? $data['stage_metrics'] : [];
            $hardwareStatus = is_array($data['hardware_status'] ?? null) ? $data['hardware_status'] : [];

            return [
                'success' => true,
                'error' => null,
                'pipeline_metrics' => $pipelineMetrics ?: $data,
                'stage_metrics' => $stageMetrics,
                'hardware_status' => $hardwareStatus,
            ];
        } catch (\Throwable $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
                'pipeline_metrics' => [],
                'stage_metrics' => [],
                'hardware_status' => [],
            ];
        }
    }

    public function getDataQualityData(): array
    {
        try {
            $response = app(MonitoringService::class)->getDataQuality();

            if (!($response['success'] ?? false)) {
                return [
                    'success' => false,
                    'error' => $response['error'] ?? 'Unbekannter Fehler',
                    'data' => [],
                ];
            }

            $data = is_array($response['data'] ?? null) ? $response['data'] : [];

            return [
                'success' => true,
                'error' => null,
                'data' => $data,
            ];
        } catch (\Throwable $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
                'data' => [],
            ];
        }
    }

    public function calculateProgress(array $metrics): float
    {
        $total = (float) ($metrics['total_documents'] ?? 0);
        $completed = (float) ($metrics['documents_completed'] ?? 0);

        if ($total <= 0) {
            return 0;
        }

        return min(100, max(0, ($completed / $total) * 100));
    }

    public function getStageStatusBadge(array $stage): array
    {
        if (!empty($stage['active'])) {
            return ['label' => 'Running', 'color' => 'warning'];
        }

        if (($stage['failed_count'] ?? 0) > 0) {
            return ['label' => 'Attention', 'color' => 'danger'];
        }

        if (!empty($stage['completed'])) {
            return ['label' => 'Completed', 'color' => 'success'];
        }

        return ['label' => 'Idle', 'color' => 'gray'];
    }

    protected function getViewData(): array
    {
        self::$pollingInterval = (string) config('krai.monitoring.polling_intervals.pipeline', '15s');

        return [
            'pipelineData' => $this->getPipelineData(),
            'qualityData' => $this->getDataQualityData(),
        ];
    }
}

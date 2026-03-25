<?php

namespace App\Filament\Pages;

use App\Services\BackendApiService;
use App\Services\MonitoringService;
use Filament\Pages\Page;

class PipelineStatusPage extends Page
{
    protected string $view = 'filament.pages.pipeline-status';

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

    public function getPipelineActivityData(): array
    {
        try {
            $queueResponse = app(MonitoringService::class)->getQueueStatus();
            $errorResponse = app(BackendApiService::class)->getErrors([
                'page' => 1,
                'page_size' => 10,
            ]);

            $queueItems = is_array($queueResponse['data']['queue_items'] ?? null)
                ? $queueResponse['data']['queue_items']
                : [];
            $errors = is_array($errorResponse['data']['errors'] ?? null)
                ? $errorResponse['data']['errors']
                : [];

            $activity = [];

            foreach ($queueItems as $item) {
                if (! is_array($item)) {
                    continue;
                }

                $activity[] = [
                    'type' => 'queue',
                    'timestamp' => $item['started_at'] ?? $item['scheduled_at'] ?? null,
                    'document_id' => $item['document_id'] ?? null,
                    'stage_name' => $item['task_type'] ?? null,
                    'status' => $item['status'] ?? 'unknown',
                    'message' => sprintf(
                        'Queue %s fuer %s',
                        $item['status'] ?? 'unknown',
                        $item['task_type'] ?? 'unknown'
                    ),
                    'priority' => $item['priority'] ?? null,
                ];
            }

            foreach ($errors as $error) {
                if (! is_array($error)) {
                    continue;
                }

                $activity[] = [
                    'type' => 'error',
                    'timestamp' => $error['created_at'] ?? null,
                    'document_id' => $error['document_id'] ?? null,
                    'stage_name' => $error['stage_name'] ?? null,
                    'status' => 'error',
                    'message' => $error['error_message'] ?? 'Pipeline-Fehler',
                    'priority' => null,
                ];
            }

            usort($activity, function (array $left, array $right): int {
                return strcmp((string) ($right['timestamp'] ?? ''), (string) ($left['timestamp'] ?? ''));
            });

            $activity = array_slice($activity, 0, 20);

            return [
                'success' => ($queueResponse['success'] ?? false) || ($errorResponse['success'] ?? false),
                'error' => $queueResponse['error'] ?? $errorResponse['error'] ?? null,
                'activity' => $activity,
                'terminal_lines' => $this->formatTerminalLines($activity),
            ];
        } catch (\Throwable $e) {
            return [
                'success' => false,
                'error' => $e->getMessage(),
                'activity' => [],
                'terminal_lines' => [],
            ];
        }
    }

    public function formatTerminalLines(array $activity): array
    {
        return array_map(function (array $entry): string {
            $timestamp = $entry['timestamp'] ?? 'unknown-time';
            $type = strtoupper((string) ($entry['type'] ?? 'activity'));
            $status = strtoupper((string) ($entry['status'] ?? 'unknown'));
            $stage = (string) ($entry['stage_name'] ?? 'unknown');
            $documentId = (string) ($entry['document_id'] ?? 'n/a');
            $message = (string) ($entry['message'] ?? 'No message');

            return sprintf('[%s] %-5s %-12s doc=%s stage=%s %s', $timestamp, $type, $status, $documentId, $stage, $message);
        }, $activity);
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
            'activityData' => $this->getPipelineActivityData(),
        ];
    }
}

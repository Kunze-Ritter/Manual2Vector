<?php

namespace App\Filament\Widgets;

use App\Services\MonitoringService;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class DataQualityWidget extends BaseWidget
{
    protected static ?int $sort = 5;

    protected function getPollingInterval(): ?string
    {
        return config('krai.monitoring.polling_intervals.data_quality', '60s');
    }

    protected function getStats(): array
    {
        $monitoringService = app(MonitoringService::class);
        $batch = $monitoringService->getDashboardBatch();
        $result = $batch['data_quality'] ?? $monitoringService->getDataQuality();

        if (!$result['success']) {
            return $this->getFallbackStats($result['error']);
        }

        $data = $result['data'];

        return [
            $this->getSuccessRateStat($data),
            $this->getValidationErrorsStat($data),
            $this->getDuplicatesStat($data),
        ];
    }

    private function getSuccessRateStat(array $data): Stat
    {
        $processingMetrics = $data['processing_metrics'] ?? [];
        $successRate = $processingMetrics['success_rate'] ?? 0;

        $color = 'danger';
        if ($successRate >= 95) {
            $color = 'success';
        } elseif ($successRate >= 90) {
            $color = 'warning';
        }

        $totalProcessed = $processingMetrics['total_processed'] ?? 0;
        $description = sprintf('Total processed: %s', number_format($totalProcessed));

        return Stat::make('Success Rate', number_format($successRate, 1) . '%')
            ->description($description)
            ->descriptionIcon('heroicon-o-check-badge')
            ->color($color)
            ->chart([
                $processingMetrics['successful'] ?? 0,
                $processingMetrics['failed'] ?? 0,
            ]);
    }

    private function getValidationErrorsStat(array $data): Stat
    {
        $validationMetrics = $data['validation_metrics'] ?? [];
        $totalErrors = $validationMetrics['total_validation_errors'] ?? 0;
        $errorsByStage = $validationMetrics['errors_by_stage'] ?? [];

        $color = 'success';
        if ($totalErrors > 0) {
            $color = 'warning';
        }
        if ($totalErrors > 100) {
            $color = 'danger';
        }

        $topErrors = array_slice($errorsByStage, 0, 2, true);
        $description = 'No validation errors';
        if (!empty($topErrors)) {
            $description = implode(', ', array_map(
                fn($stage, $count) => "$stage: $count",
                array_keys($topErrors),
                array_values($topErrors)
            ));
        }

        return Stat::make('Validation Errors', number_format($totalErrors))
            ->description($description)
            ->descriptionIcon('heroicon-o-exclamation-circle')
            ->color($color);
    }

    private function getDuplicatesStat(array $data): Stat
    {
        $duplicateMetrics = $data['duplicate_metrics'] ?? [];
        $totalDuplicates = $duplicateMetrics['total_duplicates'] ?? 0;
        $duplicateByHash = $duplicateMetrics['duplicate_by_hash'] ?? 0;
        $duplicateByFilename = $duplicateMetrics['duplicate_by_filename'] ?? 0;

        $color = 'success';
        if ($totalDuplicates > 0) {
            $color = 'warning';
        }
        if ($totalDuplicates > 50) {
            $color = 'danger';
        }

        $description = 'No duplicates';
        if ($totalDuplicates > 0) {
            $description = sprintf(
                'Hash: %d | Filename: %d',
                $duplicateByHash,
                $duplicateByFilename
            );
        }

        return Stat::make('Duplicates', number_format($totalDuplicates))
            ->description($description)
            ->descriptionIcon('heroicon-o-document-duplicate')
            ->color($color);
    }

    private function getFallbackStats(?string $error): array
    {
        return [
            Stat::make('Success Rate', 'N/A')
                ->description($error ?? 'Unable to fetch data')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
            Stat::make('Validation Errors', 'N/A')
                ->description('Offline')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
            Stat::make('Duplicates', 'N/A')
                ->description('Offline')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
        ];
    }
}

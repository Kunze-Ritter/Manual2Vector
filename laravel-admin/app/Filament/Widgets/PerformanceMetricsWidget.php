<?php

namespace App\Filament\Widgets;

use App\Services\MonitoringService;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\Log;

class PerformanceMetricsWidget extends BaseWidget
{
    protected static ?int $sort = 7;

    protected int | string | array $columnSpan = 'full';

    protected string $view = 'filament.widgets.performance-metrics';

    public function getPollingInterval(): ?string
    {
        $interval = config('krai.monitoring.polling_intervals.performance', '60s');

        return is_numeric($interval) ? "{$interval}s" : $interval;
    }

    protected function getStats(): array
    {
        $monitoringService = app(MonitoringService::class);
        $response = $monitoringService->getPerformanceMetrics();

        if (!$response['success']) {
            Log::warning('Failed to fetch performance metrics for widget', [
                'error' => $response['error'],
            ]);
            return $this->getFallbackStats();
        }

        $data = $response['data'];
        $overallImprovement = $data['overall_improvement'] ?? null;
        $stages = $data['stages'] ?? [];

        // Calculate average baseline and current times
        $baselineAvg = 0;
        $currentAvg = 0;
        $stageCount = 0;

        foreach ($stages as $stage) {
            if (isset($stage['baseline_avg_seconds']) && isset($stage['current_avg_seconds'])) {
                $baselineAvg += $stage['baseline_avg_seconds'];
                $currentAvg += $stage['current_avg_seconds'];
                $stageCount++;
            }
        }

        if ($stageCount > 0) {
            $baselineAvg = $baselineAvg / $stageCount;
            $currentAvg = $currentAvg / $stageCount;
        }

        // Determine color for overall improvement
        $improvementColor = 'danger';
        if ($overallImprovement !== null) {
            if ($overallImprovement >= 30) {
                $improvementColor = 'success';
            } elseif ($overallImprovement >= 10) {
                $improvementColor = 'warning';
            }
        }

        return [
            Stat::make('Overall Improvement', $overallImprovement !== null ? number_format($overallImprovement, 1) . '%' : 'N/A')
                ->description('Average improvement across all stages')
                ->descriptionIcon('heroicon-o-arrow-trending-up')
                ->color($improvementColor),

            Stat::make('Baseline Avg', $baselineAvg > 0 ? number_format($baselineAvg, 3) . 's' : 'N/A')
                ->description('Average baseline processing time')
                ->descriptionIcon('heroicon-o-clock')
                ->color('gray'),

            Stat::make('Current Avg', $currentAvg > 0 ? number_format($currentAvg, 3) . 's' : 'N/A')
                ->description('Average current processing time')
                ->descriptionIcon('heroicon-o-bolt')
                ->color('info'),
        ];
    }

    protected function getFallbackStats(): array
    {
        return [
            Stat::make('Overall Improvement', 'N/A')
                ->description('Data unavailable')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),

            Stat::make('Baseline Avg', 'N/A')
                ->description('Data unavailable')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),

            Stat::make('Current Avg', 'N/A')
                ->description('Data unavailable')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
        ];
    }

    protected function getViewData(): array
    {
        $monitoringService = app(MonitoringService::class);
        $response = $monitoringService->getPerformanceMetrics();

        if (!$response['success']) {
            return ['stages' => []];
        }

        $data = $response['data'];
        return ['stages' => $data['stages'] ?? []];
    }
}

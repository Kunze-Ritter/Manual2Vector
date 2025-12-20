<?php

namespace App\Filament\Widgets;

use App\Services\MonitoringService;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class SystemMetricsWidget extends BaseWidget
{
    protected static ?int $sort = 6;

    protected function getPollingInterval(): ?string
    {
        $interval = config('krai.monitoring.polling_intervals.metrics', '60s');

        return is_numeric($interval) ? "{$interval}s" : $interval;
    }

    protected function getStats(): array
    {
        $monitoringService = app(MonitoringService::class);
        $batch = $monitoringService->getDashboardBatch();
        $result = $batch['metrics'] ?? $monitoringService->getMonitoringMetrics();

        if (!$result['success']) {
            return $this->getFallbackStats($result['error']);
        }

        $data = $result['data'];
        $hardware = $data['hardware'] ?? [];

        return [
            $this->getCpuStat($hardware),
            $this->getRamStat($hardware),
            $this->getGpuStat($hardware),
        ];
    }

    private function getCpuStat(array $hardware): Stat
    {
        $cpu = $hardware['cpu_percent'] ?? 0;

        return Stat::make('CPU Usage', number_format($cpu, 1) . '%')
            ->description('Current CPU load')
            ->descriptionIcon('heroicon-o-cpu-chip')
            ->color($cpu > 80 ? 'danger' : ($cpu > 60 ? 'warning' : 'success'));
    }

    private function getRamStat(array $hardware): Stat
    {
        $ram = $hardware['ram_percent'] ?? 0;
        $ramAvailable = $hardware['ram_available_gb'] ?? null;

        $description = 'RAM usage';
        if ($ramAvailable !== null) {
            $description = sprintf('Available: %.1f GB', $ramAvailable);
        }

        return Stat::make('RAM Usage', number_format($ram, 1) . '%')
            ->description($description)
            ->descriptionIcon('heroicon-o-server-stack')
            ->color($ram > 85 ? 'danger' : ($ram > 70 ? 'warning' : 'success'));
    }

    private function getGpuStat(array $hardware): Stat
    {
        $gpuAvailable = $hardware['gpu_available'] ?? false;
        $gpuPercent = $hardware['gpu_percent'] ?? null;
        $gpuMemoryUsed = $hardware['gpu_memory_used_gb'] ?? null;
        $gpuMemoryTotal = $hardware['gpu_memory_total_gb'] ?? null;

        $value = $gpuAvailable ? 'Available' : 'Not Available';
        $description = 'GPU status';

        if ($gpuAvailable && $gpuPercent !== null) {
            $value = number_format($gpuPercent, 1) . '%';
            if ($gpuMemoryUsed !== null && $gpuMemoryTotal !== null) {
                $description = sprintf(
                    'Memory: %.1f / %.1f GB',
                    $gpuMemoryUsed,
                    $gpuMemoryTotal
                );
            } else {
                $description = 'GPU usage';
            }
        }

        $color = $gpuAvailable ? 'info' : 'gray';
        if ($gpuAvailable && $gpuPercent !== null) {
            $color = $gpuPercent > 85 ? 'danger' : ($gpuPercent > 70 ? 'warning' : 'success');
        }

        return Stat::make('GPU', $value)
            ->description($description)
            ->descriptionIcon('heroicon-o-sparkles')
            ->color($color);
    }

    private function getFallbackStats(?string $error): array
    {
        return [
            Stat::make('CPU Usage', 'N/A')
                ->description($error ?? 'Unable to fetch data')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
            Stat::make('RAM Usage', 'N/A')
                ->description('Offline')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
            Stat::make('GPU', 'N/A')
                ->description('Offline')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('danger'),
        ];
    }
}

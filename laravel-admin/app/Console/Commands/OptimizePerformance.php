<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Log;

class OptimizePerformance extends Command
{
    protected $signature = 'krai:optimize';

    protected $description = 'Optimize Laravel for production (cache routes, config, views, events)';

    public function handle(): int
    {
        $this->info('Starting performance optimization...');

        $commands = [
            'config:cache',
            'route:cache',
            'view:cache',
            'event:cache',
        ];

        foreach ($commands as $command) {
            $this->callSilent($command);
            $this->line(" - {$command} completed");
        }

        if (function_exists('opcache_get_status')) {
            $status = opcache_get_status();
            if ($status !== false) {
                $hitRate = $status['opcache_statistics']['opcache_hit_rate'] ?? null;
                $this->line(sprintf(
                    'Opcache: %s | Hit Rate: %s%% | Cached Scripts: %s',
                    $status['opcache_enabled'] ? 'enabled' : 'disabled',
                    $hitRate !== null ? number_format($hitRate, 2) : 'n/a',
                    $status['opcache_statistics']['num_cached_scripts'] ?? 'n/a',
                ));
            }
        }

        Log::info('krai:optimize completed');
        $this->info('Performance optimization completed. Routes, config, views, and events are cached.');

        return self::SUCCESS;
    }
}

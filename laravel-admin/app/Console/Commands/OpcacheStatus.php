<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;

class OpcacheStatus extends Command
{
    protected $signature = 'krai:opcache-status';

    protected $description = 'Display Opcache configuration and statistics';

    public function handle(): int
    {
        if (! function_exists('opcache_get_status')) {
            $this->warn('Opcache extension is not available.');
            return self::SUCCESS;
        }

        $status = opcache_get_status();

        if ($status === false) {
            $this->error('Failed to read Opcache status.');
            return self::FAILURE;
        }

        $config = opcache_get_configuration();
        $stats = $status['opcache_statistics'] ?? [];
        $memory = $status['memory_usage'] ?? [];

        $this->line(sprintf('Opcache enabled: %s', $status['opcache_enabled'] ? 'yes' : 'no'));
        $this->line(sprintf('Cached scripts: %s / %s', $stats['num_cached_scripts'] ?? 'n/a', $stats['max_cached_keys'] ?? 'n/a'));
        $this->line(sprintf('Hits: %s | Misses: %s | Hit Rate: %s%%', $stats['hits'] ?? 'n/a', $stats['misses'] ?? 'n/a', isset($stats['opcache_hit_rate']) ? number_format($stats['opcache_hit_rate'], 2) : 'n/a'));
        $this->line(sprintf(
            'Memory Usage (MB): Used %s | Free %s | Wasted %s',
            isset($memory['used_memory']) ? number_format($memory['used_memory'] / 1024 / 1024, 2) : 'n/a',
            isset($memory['free_memory']) ? number_format($memory['free_memory'] / 1024 / 1024, 2) : 'n/a',
            isset($memory['wasted_memory']) ? number_format($memory['wasted_memory'] / 1024 / 1024, 2) : 'n/a',
        ));

        if (isset($stats['opcache_hit_rate']) && $stats['opcache_hit_rate'] < 95) {
            $this->warn('Opcache hit rate is below 95% — consider increasing cache size or reviewing invalidations.');
        }

        if (! empty($config['directives'])) {
            $this->line('Key directives:');
            $this->line(sprintf(
                ' - memory_consumption: %s MB',
                isset($config['directives']['opcache.memory_consumption'])
                    ? $config['directives']['opcache.memory_consumption']
                    : 'n/a'
            ));
            $this->line(sprintf(
                ' - max_accelerated_files: %s',
                $config['directives']['opcache.max_accelerated_files'] ?? 'n/a'
            ));
            $this->line(sprintf(
                ' - validate_timestamps: %s',
                $config['directives']['opcache.validate_timestamps'] ?? 'n/a'
            ));
        }

        return self::SUCCESS;
    }
}

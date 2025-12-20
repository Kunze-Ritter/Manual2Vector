<?php

namespace App\Console\Commands;

use App\Services\MonitoringService;
use Illuminate\Console\Command;

class ClearAllCaches extends Command
{
    protected $signature = 'krai:cache-clear';

    protected $description = 'Clear all Laravel caches (config, routes, views, application, events)';

    public function handle(): int
    {
        $this->info('Clearing all caches...');

        $commands = [
            'config:clear',
            'route:clear',
            'view:clear',
            'cache:clear',
            'event:clear',
        ];

        foreach ($commands as $command) {
            $this->callSilent($command);
            $this->line(" - {$command} cleared");
        }

        app(MonitoringService::class)->clearCache();
        $this->line(' - monitoring cache cleared');

        $this->info('All caches cleared successfully.');

        return self::SUCCESS;
    }
}

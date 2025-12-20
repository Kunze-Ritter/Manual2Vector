<?php

namespace App\Providers;

use Illuminate\Support\Facades\Gate;
use Laravel\Telescope\Telescope;
use Laravel\Telescope\IncomingEntry;
use Laravel\Telescope\TelescopeApplicationServiceProvider;

class TelescopeServiceProvider extends TelescopeApplicationServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        Telescope::night();

        Telescope::filter(function (IncomingEntry $entry) {
            if ($this->app->environment('local', 'testing')) {
                return true;
            }

            return $entry->isReportableException() || $entry->isFailedRequest() || $entry->isFailedJob();
        });
    }

    /**
     * Configure Telescope authorization for non-local environments.
     */
    protected function gate(): void
    {
        Gate::define('viewTelescope', function ($user = null) {
            return $this->app->environment('local', 'testing');
        });
    }

    /**
     * Register any Telescope watchers.
     */
    protected function registerWatchers(): void
    {
        Telescope::filter(function ($entry) {
            return true;
        });

        Telescope::filter(function (IncomingEntry $entry) {
            if ($this->app->environment('local', 'testing')) {
                return true;
            }

            return $entry->isReportableException() || $entry->isFailedRequest() || $entry->isFailedJob();
        });

        Telescope::collect([
            Telescope::afterRecord(function (IncomingEntry $entry) {
                // No-op hook for future enrichment.
            }),
        ]);

        Telescope::startWatchers([
            \Laravel\Telescope\Watchers\RequestWatcher::class => [
                'size_limit' => 64,
            ],
            \Laravel\Telescope\Watchers\QueryWatcher::class => [
                'slow' => 100,
            ],
            \Laravel\Telescope\Watchers\CacheWatcher::class => [
                'enabled' => true,
            ],
        ]);
    }
}

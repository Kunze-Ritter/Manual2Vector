<?php

namespace App\Providers;

use App\Services\FirecrawlService;
use App\Services\KraiEngineService;
use App\Services\MonitoringService;
use App\Services\AiAgentService;
use Illuminate\Support\Facades\App;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        if (
            App::environment(['local', 'testing']) &&
            class_exists(\Laravel\Telescope\TelescopeApplicationServiceProvider::class)
        ) {
            $this->app->register('App\Providers\TelescopeServiceProvider');
        }

        $this->app->singleton(KraiEngineService::class, function ($app) {
            return new KraiEngineService(
                config('krai.engine_url'),
                config('krai.service_jwt')
            );
        });

        $this->app->singleton(MonitoringService::class, function ($app) {
            return new MonitoringService(
                config('krai.engine_url'),
                config('krai.service_jwt')
            );
        });

        $this->app->singleton(\App\Services\ImageService::class, function ($app) {
            return new \App\Services\ImageService(
                config('krai.engine_url'),
                config('krai.service_jwt')
            );
        });

        $this->app->singleton(FirecrawlService::class, function ($app) {
            return new FirecrawlService();
        });

        $this->app->singleton(AiAgentService::class, function ($app) {
            return new AiAgentService(
                config('krai.ai_agent.base_url'),
                config('krai.service_jwt')
            );
        });
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}

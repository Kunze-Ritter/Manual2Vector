<?php

namespace App\Providers;

use App\Services\KraiEngineService;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->singleton(KraiEngineService::class, function ($app) {
            return new KraiEngineService(
                config('krai.engine_url'),
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

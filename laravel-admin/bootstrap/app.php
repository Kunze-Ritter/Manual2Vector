<?php

use App\Console\Commands\BenchmarkPerformance;
use App\Console\Commands\ClearAllCaches;
use App\Console\Commands\OpcacheStatus;
use App\Console\Commands\OptimizePerformance;
use App\Http\Middleware\PerformanceProfiler;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Support\Env;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $env = Env::get('APP_ENV', 'production');
        if (Env::get('PERFORMANCE_PROFILER_ENABLED', false) || in_array($env, ['local', 'development'])) {
            $middleware->append(PerformanceProfiler::class);
        }
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        //
    })
    ->withCommands([
        BenchmarkPerformance::class,
        OptimizePerformance::class,
        ClearAllCaches::class,
        OpcacheStatus::class,
    ])
    ->create();

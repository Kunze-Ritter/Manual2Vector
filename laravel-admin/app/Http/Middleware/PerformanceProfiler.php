<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Symfony\Component\HttpFoundation\Response;

class PerformanceProfiler
{
    /**
     * Measure request execution time and memory usage.
     */
    public function handle(Request $request, Closure $next): Response
    {
        DB::enableQueryLog();
        $start = microtime(true);
        $startMemory = memory_get_usage(true);

        /** @var Response $response */
        $response = $next($request);

        $durationMs = (microtime(true) - $start) * 1000;
        $peakMemory = memory_get_peak_usage(true);
        $memoryDelta = $peakMemory - $startMemory;
        $queries = DB::getQueryLog();
        $queryCount = count($queries);

        $response->headers->set('X-Execution-Time', number_format($durationMs, 2) . 'ms');
        $response->headers->set('X-Memory-Usage', $this->formatBytes($memoryDelta));
        $response->headers->set('X-Query-Count', (string) $queryCount);

        if ($durationMs > 1000) {
            Log::warning('Slow request detected', [
                'path' => $request->path(),
                'method' => $request->method(),
                'duration_ms' => $durationMs,
                'query_count' => $queryCount,
                'peak_memory' => $this->formatBytes($peakMemory),
            ]);
        }

        return $response;
    }

    private function formatBytes(int $bytes): string
    {
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        $bytes = max($bytes, 0);
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);

        $bytes /= 1024 ** $pow;

        return round($bytes, 2) . ' ' . $units[$pow];
    }
}

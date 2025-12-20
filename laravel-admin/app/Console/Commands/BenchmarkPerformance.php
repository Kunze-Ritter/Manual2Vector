<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Arr;

class BenchmarkPerformance extends Command
{
    protected $signature = 'krai:benchmark {--iterations=10}';

    protected $description = 'Benchmark key dashboard endpoints and report latency statistics';

    private array $endpoints = [
        'dashboard' => '/kradmin',
        'documents' => '/documents',
        'monitoring' => '/monitoring/dashboard',
        'api_status' => '/monitoring/api-status',
    ];

    public function handle(): int
    {
        $iterations = (int) $this->option('iterations');
        if ($iterations < 1) {
            $this->error('Iterations must be >= 1');
            return self::FAILURE;
        }

        $baseUrl = rtrim(config('app.url', 'http://localhost'), '/');
        $results = [];

        foreach ($this->endpoints as $name => $path) {
            $durations = [];
            for ($i = 0; $i < $iterations; $i++) {
                $start = microtime(true);
                try {
                    Http::timeout(10)->get($baseUrl . $path);
                } catch (\Throwable $e) {
                    // Ignore individual failures; record as 0 for visibility
                }
                $durations[] = (microtime(true) - $start) * 1000;
            }

            sort($durations);
            $results[] = [
                'Endpoint' => $name,
                'Min (ms)' => number_format($durations[0], 2),
                'Max (ms)' => number_format($durations[array_key_last($durations)], 2),
                'Avg (ms)' => number_format(array_sum($durations) / $iterations, 2),
                'p50 (ms)' => number_format($this->percentile($durations, 50), 2),
                'p90 (ms)' => number_format($this->percentile($durations, 90), 2),
            ];
        }

        $this->table(
            array_keys($results[0] ?? []),
            $results
        );

        return self::SUCCESS;
    }

    private function percentile(array $values, float $percentile): float
    {
        if (empty($values)) {
            return 0.0;
        }

        $index = (int) ceil(($percentile / 100) * count($values)) - 1;

        return Arr::get($values, max($index, 0), 0.0);
    }
}

<?php

namespace App\Services;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class FirecrawlService
{
    private string $firecrawlUrl;
    private string $backendUrl;
    private ?string $serviceJwt;

    public function __construct()
    {
        $this->firecrawlUrl = rtrim(config('krai.firecrawl.api_url', env('FIRECRAWL_API_URL', 'http://krai-firecrawl-api-prod:8002')), '/');
        $this->backendUrl = rtrim(config('krai.engine_url', env('KRAI_ENGINE_URL', 'http://krai-engine:8000')), '/');
        $this->serviceJwt = config('krai.service_jwt');
    }

    protected function logChannel()
    {
        return Log::channel('firecrawl');
    }

    protected function healthTimeout(): int
    {
        return (int) config('krai.firecrawl.timeout.health', 10);
    }

    protected function operationTimeout(): int
    {
        return (int) config('krai.firecrawl.timeout.scrape', 30);
    }

    protected function crawlTimeout(): int
    {
        return (int) config('krai.firecrawl.timeout.crawl', 300);
    }

    protected function cacheTtl(): int
    {
        return (int) config('krai.firecrawl.cache_ttl', 60);
    }

    protected function createHttpClient(int $timeout, bool $withAuth = false)
    {
        $client = Http::timeout($timeout)->acceptJson();

        if ($withAuth && $this->serviceJwt) {
            $client = $client->withHeaders([
                'Authorization' => 'Bearer ' . $this->serviceJwt,
            ]);
        }

        return $client;
    }

    public function getHealth(): array
    {
        return Cache::remember('firecrawl.health', $this->cacheTtl(), function () {
            try {
                $response = $this->callBackend('get', '/api/v1/scraping/health', [], $this->healthTimeout());

                if ($response['success'] ?? false) {
                    return [
                        'success' => true,
                        'data' => $response['data'],
                        'error' => null,
                    ];
                }

                return [
                    'success' => false,
                    'data' => [],
                    'error' => $response['error'] ?? 'Health check failed',
                ];
            } catch (\Throwable $e) {
                $this->logChannel()->warning('Firecrawl backend health failed, trying direct health fallback', [
                    'message' => $e->getMessage(),
                ]);

                try {
                    $direct = $this->createHttpClient($this->healthTimeout())->get("{$this->firecrawlUrl}/");
                    if ($direct->successful()) {
                        return [
                            'success' => true,
                            'data' => [
                                'status' => 'healthy',
                                'version' => null,
                                'backend' => 'firecrawl',
                                'capabilities' => ['scrape', 'crawl', 'extract', 'map'],
                            ],
                            'error' => null,
                        ];
                    }

                    return [
                        'success' => false,
                        'data' => [],
                        'error' => "HTTP {$direct->status()}: {$direct->body()}",
                    ];
                } catch (\Throwable $fallback) {
                    $this->logChannel()->error('Firecrawl direct health fallback failed', [
                        'message' => $fallback->getMessage(),
                    ]);

                    return [
                        'success' => false,
                        'data' => [],
                        'error' => $fallback->getMessage(),
                    ];
                }
            } catch (\Throwable $e) {
                $this->logChannel()->error('Firecrawl health exception', [
                    'message' => $e->getMessage(),
                ]);

                return [
                    'success' => false,
                    'data' => [],
                    'error' => $e->getMessage(),
                ];
            }
        });
    }

    public function getBackendInfo(): array
    {
        return $this->callBackend('get', '/api/v1/scraping/info', [], 10);
    }

    public function getConfiguration(): array
    {
        $response = $this->callBackend('get', '/api/v1/scraping/config', [], 10);

        if ($response['success'] ?? false) {
            return $response['data']['config'] ?? [];
        }

        // Fallback to static config for display
        return [
            'api_url' => $this->firecrawlUrl,
            'provider' => config('krai.firecrawl.llm_provider'),
            'model_name' => config('krai.firecrawl.model_name'),
            'embedding_model' => config('krai.firecrawl.embedding_model'),
            'max_concurrency' => config('krai.firecrawl.max_concurrency'),
            'block_media' => config('krai.firecrawl.block_media'),
            'test_urls' => config('krai.firecrawl.test_urls'),
        ];
    }

    public function updateConfiguration(array $config): array
    {
        return $this->callBackend('put', '/api/v1/scraping/config', $config, 10);
    }

    public function getRecentActivity(int $limit = 50): array
    {
        return Cache::remember("firecrawl.activity.{$limit}", $this->cacheTtl(), function () use ($limit) {
            return $this->callBackend('get', '/api/v1/scraping/logs', ['limit' => $limit], 10);
        });
    }

    public function scrapeUrl(string $url, array $options = []): array
    {
        return $this->postFirecrawl('/scrape', ['url' => $url, 'options' => $options], $this->operationTimeout());
    }

    public function crawlSite(string $url, array $options = []): array
    {
        return $this->postFirecrawl('/crawl', ['url' => $url, 'options' => $options], $this->crawlTimeout());
    }

    public function extractStructured(string $url, array $schema, array $options = []): array
    {
        return $this->postFirecrawl('/extract', ['url' => $url, 'schema' => $schema, 'options' => $options], $this->operationTimeout());
    }

    public function mapUrls(string $url, array $options = []): array
    {
        return $this->postFirecrawl('/map', ['url' => $url, 'options' => $options], $this->operationTimeout());
    }

    public function scrapeViaBackend(string $url, array $options = [], ?string $forceBackend = null): array
    {
        $payload = ['url' => $url, 'options' => $options];
        if ($forceBackend) {
            $payload['force_backend'] = $forceBackend;
        }

        return $this->callBackend('post', '/api/v1/scraping/scrape', $payload, $this->operationTimeout());
    }

    public function crawlViaBackend(string $url, array $options = [], ?string $forceBackend = null): array
    {
        $payload = ['start_url' => $url, 'options' => $options];
        if ($forceBackend) {
            $payload['force_backend'] = $forceBackend;
        }

        return $this->callBackend('post', '/api/v1/scraping/crawl', $payload, $this->crawlTimeout());
    }

    public function extractViaBackend(string $url, array $schema, array $options = [], ?string $forceBackend = null): array
    {
        $payload = ['url' => $url, 'schema' => $schema, 'options' => $options];
        if ($forceBackend) {
            $payload['force_backend'] = $forceBackend;
        }

        return $this->callBackend('post', '/api/v1/scraping/extract', $payload, $this->operationTimeout());
    }

    public function mapViaBackend(string $url, array $options = [], ?string $forceBackend = null): array
    {
        $payload = ['url' => $url, 'options' => $options];
        if ($forceBackend) {
            $payload['force_backend'] = $forceBackend;
        }

        return $this->callBackend('post', '/api/v1/scraping/map', $payload, $this->operationTimeout());
    }

    protected function postFirecrawl(string $path, array $payload, int $timeout): array
    {
        try {
            $response = $this->createHttpClient($timeout)
                ->post("{$this->firecrawlUrl}{$path}", $payload);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json(),
                    'error' => null,
                ];
            }

            $this->logChannel()->warning('Firecrawl operation failed', [
                'path' => $path,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => "HTTP {$response->status()}: {$response->body()}",
            ];
        } catch (\Throwable $e) {
            $this->logChannel()->error('Firecrawl operation exception', [
                'path' => $path,
                'message' => $e->getMessage(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => $e->getMessage(),
            ];
        }
    }

    protected function callBackend(string $method, string $path, array $params = [], int $timeout = 10): array
    {
        try {
            $client = $this->createHttpClient($timeout, true);
            $response = $client->{$method}("{$this->backendUrl}{$path}", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json(),
                    'error' => null,
                ];
            }

            $this->logChannel()->warning('Backend scraping call failed', [
                'path' => $path,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => "HTTP {$response->status()}: {$response->body()}",
            ];
        } catch (\Throwable $e) {
            $this->logChannel()->error('Backend scraping call exception', [
                'path' => $path,
                'message' => $e->getMessage(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => $e->getMessage(),
            ];
        }
    }
}

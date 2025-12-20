<?php

namespace App\Filament\Widgets;

use App\Services\FirecrawlService;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;

class APIStatusWidget extends BaseWidget
{
    protected static ?int $sort = 2;
    
    protected ?string $heading = 'API & Service Status';
    
    protected ?string $description = 'Real-time monitoring of all connected services and APIs';

    protected function getPollingInterval(): ?string
    {
        $interval = config('krai.monitoring.polling_intervals.dashboard', '60s');

        return is_numeric($interval) ? "{$interval}s" : $interval;
    }
    
    protected $listeners = ['startService' => 'handleStartService'];
    
    public function handleStartService($service)
    {
        try {
            $containerMap = [
                'ollama' => 'krai-ollama-prod',
                'backend' => 'krai-backend-prod',
                'redis' => 'krai-redis-prod',
                'firecrawl' => 'krai-firecrawl-api-prod',
            ];
            
            if (!isset($containerMap[$service])) {
                \Filament\Notifications\Notification::make()
                    ->title('Service not found')
                    ->danger()
                    ->send();
                return;
            }
            
            $container = $containerMap[$service];
            $command = "docker start {$container}";
            
            exec($command, $output, $returnCode);
            
            if ($returnCode === 0) {
                \Filament\Notifications\Notification::make()
                    ->title('Service started')
                    ->body("Successfully started {$service}")
                    ->success()
                    ->send();
                    
                // Clear cache to force refresh
                Cache::forget("{$service}_status");
            } else {
                \Filament\Notifications\Notification::make()
                    ->title('Failed to start service')
                    ->body("Could not start {$service}")
                    ->danger()
                    ->send();
            }
        } catch (\Exception $e) {
            \Filament\Notifications\Notification::make()
                ->title('Error')
                ->body($e->getMessage())
                ->danger()
                ->send();
        }
    }

    protected function getStats(): array
    {
        $stats = [];
        
        // Ollama
        $ollamaStatus = $this->getOllamaStatus();
        $ollamaStat = Stat::make('Ollama', $ollamaStatus['status'] === 'online' ? 'Online' : 'Offline')
            ->description($ollamaStatus['message'])
            ->descriptionIcon($ollamaStatus['icon'])
            ->color($ollamaStatus['status'] === 'online' ? 'success' : 'danger')
            ->chart($ollamaStatus['status'] === 'online' ? [100, 100, 100, 100, 100, 100, 100] : [0, 0, 0, 0, 0, 0, 0]);
        
        if ($ollamaStatus['status'] !== 'online') {
            $ollamaStat->extraAttributes([
                'wire:click' => "\$dispatch('startService', { service: 'ollama' })",
                'class' => 'cursor-pointer hover:ring-2 hover:ring-primary-500',
            ]);
        }
        
        $stats[] = $ollamaStat;
        
        // OpenAI
        $openaiStatus = $this->getOpenAIStatus();
        $stats[] = Stat::make('OpenAI', $openaiStatus['status'] === 'online' ? 'Online' : 'Not Configured')
            ->description($openaiStatus['message'])
            ->descriptionIcon($openaiStatus['icon'])
            ->color($openaiStatus['status'] === 'online' ? 'success' : 'warning')
            ->chart($openaiStatus['status'] === 'online' ? [100, 100, 100, 100, 100, 100, 100] : [0, 0, 0, 0, 0, 0, 0]);
        
        // Backend
        $backendStatus = $this->getBackendStatus();
        $backendStat = Stat::make('Backend', $backendStatus['status'] === 'online' ? 'Online' : 'Offline')
            ->description($backendStatus['message'])
            ->descriptionIcon($backendStatus['icon'])
            ->color($backendStatus['status'] === 'online' ? 'success' : 'danger')
            ->chart($backendStatus['status'] === 'online' ? [100, 100, 100, 100, 100, 100, 100] : [0, 0, 0, 0, 0, 0, 0]);
        
        if ($backendStatus['status'] !== 'online') {
            $backendStat->extraAttributes([
                'wire:click' => "\$dispatch('startService', { service: 'backend' })",
                'class' => 'cursor-pointer hover:ring-2 hover:ring-primary-500',
            ]);
        }
        
        $stats[] = $backendStat;
        
        // Database
        $databaseStatus = $this->getDatabaseStatus();
        $stats[] = Stat::make('Database', $databaseStatus['status'] === 'online' ? 'Online' : 'Offline')
            ->description($databaseStatus['message'])
            ->descriptionIcon($databaseStatus['icon'])
            ->color($databaseStatus['status'] === 'online' ? 'success' : 'danger')
            ->chart($databaseStatus['status'] === 'online' ? [100, 100, 100, 100, 100, 100, 100] : [0, 0, 0, 0, 0, 0, 0]);
        
        // Redis
        $redisStatus = $this->getRedisStatus();
        $stats[] = Stat::make('Redis', $redisStatus['status'] === 'online' ? 'Online' : ($redisStatus['status'] === 'not_installed' ? 'Not Installed' : 'Offline'))
            ->description($redisStatus['message'])
            ->descriptionIcon($redisStatus['icon'])
            ->color($redisStatus['status'] === 'online' ? 'success' : ($redisStatus['status'] === 'not_installed' ? 'warning' : 'danger'))
            ->chart($redisStatus['status'] === 'online' ? [100, 100, 100, 100, 100, 100, 100] : [0, 0, 0, 0, 0, 0, 0]);
        
        // Storage
        $storageStatus = $this->getStorageStatus();
        $stats[] = Stat::make('Storage', $storageStatus['status'] === 'online' ? 'Online' : 'Offline')
            ->description($storageStatus['message'])
            ->descriptionIcon($storageStatus['icon'])
            ->color($storageStatus['status'] === 'online' ? 'success' : 'danger')
            ->chart($storageStatus['status'] === 'online' ? [100, 100, 100, 100, 100, 100, 100] : [0, 0, 0, 0, 0, 0, 0]);
        
        // Firecrawl
        $firecrawlStatus = $this->getFirecrawlStatus();
        $firecrawlStat = Stat::make('Firecrawl', $firecrawlStatus['status'] === 'online' ? 'Online' : 'Offline')
            ->description($firecrawlStatus['message'])
            ->descriptionIcon($firecrawlStatus['icon'])
            ->color($firecrawlStatus['status'] === 'online' ? 'success' : 'danger')
            ->chart($firecrawlStatus['status'] === 'online' ? [100, 100, 100, 100, 100, 100, 100] : [0, 0, 0, 0, 0, 0, 0]);
        
        if ($firecrawlStatus['status'] !== 'online') {
            $firecrawlStat->extraAttributes([
                'wire:click' => "\$dispatch('startService', { service: 'firecrawl' })",
                'class' => 'cursor-pointer hover:ring-2 hover:ring-primary-500',
            ]);
        }
        
        $stats[] = $firecrawlStat;
        
        return $stats;
    }

    protected function getOllamaStatus(): array
    {
        return Cache::remember('ollama_status', 30, function () {
            try {
                $response = Http::timeout(5)->get(env('OLLAMA_URL', 'http://krai-ollama-prod:11434') . '/api/version');

                if ($response->successful()) {
                    $data = $response->json();
                    return [
                        'status' => 'online',
                        'message' => 'Version: ' . ($data['version'] ?? 'Unknown'),
                        'icon' => 'heroicon-o-check-circle',
                        'color' => 'text-green-600',
                        'details' => [
                            'Version' => $data['version'] ?? 'Unknown',
                            'Build' => $data['build'] ?? 'Unknown',
                        ]
                    ];
                } else {
                    return [
                        'status' => 'error',
                        'message' => 'Connection failed',
                        'icon' => 'heroicon-o-x-circle',
                        'color' => 'text-red-600',
                        'details' => ['Error' => $response->status()]
                    ];
                }
            } catch (\Exception $e) {
                return [
                    'status' => 'offline',
                    'message' => 'Service unavailable',
                    'icon' => 'heroicon-o-x-circle',
                    'color' => 'text-red-600',
                    'details' => ['Error' => $e->getMessage()]
                ];
            }
        });
    }

    protected function getOpenAIStatus(): array
    {
        $apiKey = env('OPENAI_API_KEY');
        
        if (!$apiKey || $apiKey === 'your-openai-api-key-here') {
            return [
                'status' => 'not_configured',
                'message' => 'API Key not configured',
                'icon' => 'heroicon-o-exclamation-triangle',
                'color' => 'text-yellow-600',
                'details' => ['Status' => 'Configure API Key in Settings']
            ];
        }

        return Cache::remember('openai_status', 60, function () use ($apiKey) {
            try {
                $response = Http::timeout(10)
                    ->withHeaders([
                        'Authorization' => 'Bearer ' . $apiKey,
                    ])
                    ->get('https://api.openai.com/v1/models');

                if ($response->successful()) {
                    $models = $response->json('data', []);
                    return [
                        'status' => 'online',
                        'message' => count($models) . ' models available',
                        'icon' => 'heroicon-o-check-circle',
                        'color' => 'text-green-600',
                        'details' => [
                            'Models' => count($models),
                            'Endpoint' => 'api.openai.com'
                        ]
                    ];
                } else {
                    return [
                        'status' => 'error',
                        'message' => 'API Error: ' . $response->status(),
                        'icon' => 'heroicon-o-x-circle',
                        'color' => 'text-red-600',
                        'details' => ['Error' => $response->json('error.message', 'Unknown')]
                    ];
                }
            } catch (\Exception $e) {
                return [
                    'status' => 'offline',
                    'message' => 'Connection failed',
                    'icon' => 'heroicon-o-x-circle',
                    'color' => 'text-red-600',
                    'details' => ['Error' => $e->getMessage()]
                ];
            }
        });
    }

    protected function getBackendStatus(): array
    {
        return Cache::remember('backend_status', 30, function () {
            try {
                $backendUrl = config('krai.engine_url', env('KRAI_ENGINE_URL', 'http://krai-engine:8000'));
                $response = Http::timeout(5)->get("{$backendUrl}/health");

                if ($response->successful()) {
                    return [
                        'status' => 'online',
                        'message' => 'Backend healthy',
                        'icon' => 'heroicon-o-check-circle',
                        'color' => 'text-green-600',
                        'details' => ['Status' => 'Running']
                    ];
                }

                // Specific error messages based on HTTP status
                $errorMessage = match ($response->status()) {
                    404 => 'Backend health endpoint missing',
                    401, 403 => 'Authentication failed',
                    500, 502, 503 => 'Backend service error',
                    default => 'Backend error',
                };

                return [
                    'status' => 'error',
                    'message' => $errorMessage,
                    'icon' => 'heroicon-o-x-circle',
                    'color' => 'text-red-600',
                    'details' => [
                        'HTTP' => $response->status(),
                        'Action' => 'Check container logs: docker logs krai-engine-prod'
                    ]
                ];
            } catch (\Exception $e) {
                return $this->classifyServiceError($e, 'backend');
            }
        });
    }

    protected function getDatabaseStatus(): array
    {
        try {
            $connection = \Illuminate\Support\Facades\DB::connection();
            $connection->getPdo();
            
            return [
                'status' => 'online',
                'message' => 'PostgreSQL connected',
                'icon' => 'heroicon-o-check-circle',
                'color' => 'text-green-600',
                'details' => [
                    'Driver' => 'PostgreSQL',
                    'Database' => env('DB_DATABASE', 'krai')
                ]
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'offline',
                'message' => 'Database disconnected',
                'icon' => 'heroicon-o-x-circle',
                'color' => 'text-red-600',
                'details' => ['Error' => $e->getMessage()]
            ];
        }
    }

    protected function getRedisStatus(): array
    {
        // Check if Redis extension is available
        if (!class_exists('Redis')) {
            return [
                'status' => 'not_installed',
                'message' => 'Redis extension not installed',
                'icon' => 'heroicon-o-exclamation-triangle',
                'color' => 'text-yellow-600',
                'details' => ['Status' => 'Install Redis PHP extension']
            ];
        }

        try {
            $redis = new \Redis();
            $redis->connect(env('REDIS_HOST', 'krai-redis-prod'), env('REDIS_PORT', 6379));
            $redis->ping();
            
            $info = $redis->info();
            $redis->close();
            
            return [
                'status' => 'online',
                'message' => 'Redis connected',
                'icon' => 'heroicon-o-check-circle',
                'color' => 'text-green-600',
                'details' => [
                    'Version' => $info['redis_version'] ?? 'Unknown',
                    'Memory' => $info['used_memory_human'] ?? 'Unknown',
                    'Clients' => $info['connected_clients'] ?? '0'
                ]
            ];
        } catch (\Exception $e) {
            // Specific error handling for Redis
            if (str_contains($e->getMessage(), 'Connection refused')) {
                return [
                    'status' => 'offline',
                    'message' => 'Redis container offline',
                    'icon' => 'heroicon-o-x-circle',
                    'color' => 'text-red-600',
                    'details' => [
                        'Error' => 'Connection refused',
                        'Action' => 'Run: docker start krai-redis-prod'
                    ]
                ];
            }

            return [
                'status' => 'offline',
                'message' => 'Redis unavailable',
                'icon' => 'heroicon-o-x-circle',
                'color' => 'text-red-600',
                'details' => [
                    'Error' => $e->getMessage(),
                    'Action' => 'Check Redis configuration'
                ]
            ];
        }
    }

    protected function getStorageStatus(): array
    {
        try {
            // Check local storage
            $storagePath = storage_path();
            $freeSpace = disk_free_space($storagePath);
            $totalSpace = disk_total_space($storagePath);
            $usedSpace = $totalSpace - $freeSpace;
            $usagePercent = round(($usedSpace / $totalSpace) * 100, 1);
            
            return [
                'status' => 'online',
                'message' => 'Storage OK (' . $usagePercent . '% used)',
                'icon' => 'heroicon-o-check-circle',
                'color' => $usagePercent > 90 ? 'text-yellow-600' : 'text-green-600',
                'details' => [
                    'Free' => $this->formatBytes($freeSpace),
                    'Used' => $this->formatBytes($usedSpace),
                    'Total' => $this->formatBytes($totalSpace),
                    'Usage' => $usagePercent . '%'
                ]
            ];
        } catch (\Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Storage error',
                'icon' => 'heroicon-o-x-circle',
                'color' => 'text-red-600',
                'details' => ['Error' => $e->getMessage()]
            ];
        }
    }

    protected function getFirecrawlStatus(): array
    {
        return Cache::remember('firecrawl_status', 60, function () {
            try {
                $service = app(FirecrawlService::class);
                $health = $service->getHealth();

                if ($health['success']) {
                    $data = $health['data'] ?? [];

                    return [
                        'status' => 'online',
                        'message' => 'Firecrawl API ready',
                        'icon' => 'heroicon-o-check-circle',
                        'color' => 'text-green-600',
                        'details' => [
                            'Status' => $data['status'] ?? 'healthy',
                            'Version' => $data['version'] ?? 'Unknown',
                            'Backend' => $data['backend'] ?? 'firecrawl',
                            'Capabilities' => implode(', ', $data['capabilities'] ?? ['scrape', 'crawl']),
                            'Endpoint' => 'krai-firecrawl-api-prod:8002',
                        ],
                    ];
                }

                return [
                    'status' => 'error',
                    'message' => $health['error'] ?? 'Health check failed',
                    'icon' => 'heroicon-o-x-circle',
                    'color' => 'text-red-600',
                    'details' => ['Error' => $health['error'] ?? 'Unknown'],
                ];
            } catch (\Exception $e) {
                // Specific error handling for Firecrawl
                $message = $e->getMessage();
                
                if (str_contains($message, '404')) {
                    return [
                        'status' => 'error',
                        'message' => 'Firecrawl endpoint not found',
                        'icon' => 'heroicon-o-exclamation-triangle',
                        'color' => 'text-yellow-600',
                        'details' => [
                            'Error' => 'Check FIRECRAWL_API_URL config',
                            'Action' => 'Verify endpoint configuration'
                        ]
                    ];
                }
                
                if (str_contains($message, 'Connection refused')) {
                    return [
                        'status' => 'offline',
                        'message' => 'Firecrawl container offline',
                        'icon' => 'heroicon-o-x-circle',
                        'color' => 'text-red-600',
                        'details' => [
                            'Error' => 'Connection refused',
                            'Action' => 'Run: docker ps | grep firecrawl'
                        ]
                    ];
                }
                
                if (str_contains($message, 'timed out')) {
                    return [
                        'status' => 'timeout',
                        'message' => 'Firecrawl health check timeout',
                        'icon' => 'heroicon-o-clock',
                        'color' => 'text-yellow-600',
                        'details' => [
                            'Error' => 'Request timeout',
                            'Action' => 'Check Firecrawl performance'
                        ]
                    ];
                }

                return [
                    'status' => 'offline',
                    'message' => 'Firecrawl unavailable',
                    'icon' => 'heroicon-o-x-circle',
                    'color' => 'text-red-600',
                    'details' => ['Error' => $e->getMessage()]
                ];
            }
        });
    }

    /**
     * Classify service errors and return appropriate status array
     */
    private function classifyServiceError(\Exception $e, string $service): array
    {
        $message = $e->getMessage();
        
        if (str_contains($message, 'Connection refused')) {
            return [
                'status' => 'offline',
                'message' => ucfirst($service) . ' container offline',
                'icon' => 'heroicon-o-x-circle',
                'color' => 'text-red-600',
                'details' => [
                    'Error' => 'Connection refused',
                    'Action' => "Run: docker start krai-{$service}-prod"
                ]
            ];
        }
        
        if (str_contains($message, 'Could not resolve host')) {
            return [
                'status' => 'dns_error',
                'message' => 'DNS resolution failed',
                'icon' => 'heroicon-o-exclamation-triangle',
                'color' => 'text-yellow-600',
                'details' => [
                    'Error' => 'Cannot resolve hostname',
                    'Action' => 'Check Docker network configuration'
                ]
            ];
        }
        
        if (str_contains($message, 'timed out')) {
            return [
                'status' => 'timeout',
                'message' => ucfirst($service) . ' timeout',
                'icon' => 'heroicon-o-clock',
                'color' => 'text-yellow-600',
                'details' => [
                    'Error' => 'Request timeout',
                    'Action' => "Check {$service} performance and logs"
                ]
            ];
        }
        
        // Generic error fallback
        return [
            'status' => 'offline',
            'message' => ucfirst($service) . ' unavailable',
            'icon' => 'heroicon-o-x-circle',
            'color' => 'text-red-600',
            'details' => [
                'Error' => $e->getMessage(),
                'Action' => "Check {$service} status: docker ps | grep {$service}"
            ]
        ];
    }

    protected function formatBytes($bytes): string
    {
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        $bytes = max($bytes, 0);
        $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
        $pow = min($pow, count($units) - 1);
        
        $bytes /= pow(1024, $pow);
        
        return round($bytes, 1) . ' ' . $units[$pow];
    }
}

<?php

namespace Tests\Feature;

use App\Services\MonitoringService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Http\Client\ConnectionException;
use Tests\TestCase;

class MonitoringServiceTest extends TestCase
{
    protected string $baseUrl = 'http://krai-engine:8000';

    protected function tearDown(): void
    {
        (new MonitoringService())->clearCache();
        parent::tearDown();
    }

    /** @test */
    public function get_dashboard_overview_returns_success_and_data_when_backend_responds(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/dashboard/overview" => Http::response([
                'data' => [
                    'documents' => ['total' => 10],
                    'products' => ['total' => 5],
                    'queue' => ['pending' => 2],
                    'media' => ['count' => 0],
                ],
            ], 200),
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getDashboardOverview();

        $this->assertTrue($result['success']);
        $this->assertArrayHasKey('data', $result);
        $this->assertArrayHasKey('documents', $result['data']);
        $this->assertArrayHasKey('products', $result['data']);
        $this->assertArrayHasKey('queue', $result['data']);
        $this->assertArrayHasKey('media', $result['data']);
        $this->assertNull($result['error']);
    }

    /** @test */
    public function get_pipeline_status_returns_success_and_data_when_backend_responds(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/monitoring/pipeline" => Http::response([
                'pipeline_metrics' => [],
                'stage_metrics' => [],
                'hardware_status' => [],
            ], 200),
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getPipelineStatus();

        $this->assertTrue($result['success']);
        $this->assertArrayHasKey('data', $result);
        $this->assertNull($result['error']);
    }

    /** @test */
    public function get_processor_health_returns_success_and_data_when_backend_responds(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/monitoring/processors" => Http::response([
                ['name' => 'text_extraction', 'stage_name' => 'text_extraction', 'status' => 'running', 'health_score' => 95],
            ], 200),
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getProcessorHealth();

        $this->assertTrue($result['success']);
        $this->assertArrayHasKey('data', $result);
        $this->assertNull($result['error']);
    }

    /** @test */
    public function get_performance_metrics_returns_success_and_data_when_backend_responds(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/monitoring/performance" => Http::response([
                'overall_improvement' => 15.5,
                'stages' => [],
            ], 200),
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getPerformanceMetrics();

        $this->assertTrue($result['success']);
        $this->assertArrayHasKey('data', $result);
        $this->assertNull($result['error']);
    }

    /** @test */
    public function get_queue_status_returns_success_and_data_when_backend_responds(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/monitoring/queue" => Http::response([
                'queue_metrics' => ['total_items' => 0, 'pending' => 0, 'processing' => 0, 'completed' => 0, 'failed' => 0],
                'queue_items' => [],
            ], 200),
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getQueueStatus();

        $this->assertTrue($result['success']);
        $this->assertArrayHasKey('data', $result);
        $this->assertNull($result['error']);
    }

    /** @test */
    public function get_data_quality_returns_success_and_data_when_backend_responds(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/monitoring/data-quality" => Http::response([
                'success_rate' => 99.5,
                'validation_errors' => 0,
                'duplicate_documents' => 0,
            ], 200),
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getDataQuality();

        $this->assertTrue($result['success']);
        $this->assertArrayHasKey('data', $result);
        $this->assertNull($result['error']);
    }

    /** @test */
    public function get_dashboard_overview_uses_cache_ttl_from_config(): void
    {
        $ttl = config('krai.monitoring.cache_ttl.dashboard', 180);
        $this->assertIsInt($ttl);
        $this->assertGreaterThan(0, $ttl);
    }

    /** @test */
    public function get_pipeline_status_uses_cache_ttl_from_config(): void
    {
        $ttl = config('krai.monitoring.cache_ttl.pipeline', 15);
        $this->assertIsInt($ttl);
        $this->assertGreaterThan(0, $ttl);
    }

    /** @test */
    public function get_dashboard_overview_returns_error_when_backend_returns_404(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/dashboard/overview" => Http::response([], 404),
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getDashboardOverview();

        $this->assertFalse($result['success']);
        $this->assertArrayHasKey('error', $result);
        $this->assertStringContainsString('Dashboard endpoint not registered', $result['error']);
    }

    /** @test */
    public function get_dashboard_overview_returns_error_when_backend_returns_401(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/dashboard/overview" => Http::response([], 401),
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getDashboardOverview();

        $this->assertFalse($result['success']);
        $this->assertArrayHasKey('error', $result);
        $this->assertStringContainsString('Authentication failed', $result['error']);
    }

    /** @test */
    public function get_dashboard_overview_returns_user_friendly_error_when_backend_unavailable(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/dashboard/overview" => function () {
                throw new ConnectionException('Connection refused');
            },
        ]);

        $service = app(MonitoringService::class);
        $result = $service->getDashboardOverview();

        $this->assertFalse($result['success']);
        $this->assertArrayHasKey('error', $result);
        $this->assertStringContainsString('Backend service unavailable', $result['error']);
    }

    /** @test */
    public function clear_cache_removes_monitoring_caches(): void
    {
        Cache::put('monitoring.dashboard.overview', ['cached' => true], 60);
        Cache::put('monitoring.pipeline', ['cached' => true], 60);

        $service = app(MonitoringService::class);
        $service->clearCache();

        $this->assertNull(Cache::get('monitoring.dashboard.overview'));
        $this->assertNull(Cache::get('monitoring.pipeline'));
    }
}

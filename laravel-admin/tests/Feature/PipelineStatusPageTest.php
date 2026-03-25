<?php

namespace Tests\Feature;

use App\Filament\Pages\PipelineStatusPage;
use App\Services\BackendApiService;
use App\Services\MonitoringService;
use Mockery;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class PipelineStatusPageTest extends TestCase
{
    #[Test]
    public function pipeline_status_page_exposes_pipeline_activity_and_terminal_lines(): void
    {
        $monitoring = Mockery::mock(MonitoringService::class);
        $monitoring->shouldReceive('getQueueStatus')
            ->once()
            ->andReturn([
                'success' => true,
                'data' => [
                    'queue_items' => [
                        [
                            'document_id' => 'doc-1',
                            'task_type' => 'upload_processor',
                            'status' => 'pending',
                            'priority' => 5,
                            'scheduled_at' => '2026-03-25T12:00:00Z',
                        ],
                    ],
                ],
                'error' => null,
            ]);

        $backend = Mockery::mock(BackendApiService::class);
        $backend->shouldReceive('getErrors')
            ->once()
            ->with([
                'page' => 1,
                'page_size' => 10,
            ])
            ->andReturn([
                'success' => true,
                'data' => [
                    'errors' => [
                        [
                            'document_id' => 'doc-2',
                            'stage_name' => 'embedding',
                            'error_message' => 'Embedding worker failed',
                            'created_at' => '2026-03-25T12:01:00Z',
                        ],
                    ],
                ],
                'error' => null,
            ]);

        app()->instance(MonitoringService::class, $monitoring);
        app()->instance(BackendApiService::class, $backend);

        $page = app(PipelineStatusPage::class);
        $data = $page->getPipelineActivityData();

        $this->assertTrue($data['success']);
        $this->assertCount(2, $data['activity']);
        $this->assertNotEmpty($data['terminal_lines']);
        $this->assertStringContainsString('upload_processor', implode("\n", $data['terminal_lines']));
        $this->assertStringContainsString('Embedding worker failed', implode("\n", $data['terminal_lines']));
    }
}

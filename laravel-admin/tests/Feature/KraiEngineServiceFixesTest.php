<?php

namespace Tests\Feature;

use App\Services\KraiEngineService;
use Illuminate\Http\Client\Request;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class KraiEngineServiceFixesTest extends TestCase
{
    private string $baseUrl = 'http://krai-engine:8000';

    private function makeService(int $uploadTimeout = 600): KraiEngineService
    {
        return new KraiEngineService($this->baseUrl, 'test-token', 120, 60, $uploadTimeout);
    }

    #[Test]
    public function upload_document_calls_correct_url_and_does_not_force_json_content_type(): void
    {
        Http::fake([
            "{$this->baseUrl}/upload" => Http::response([
                'document_id' => 'doc-123',
                'filename' => 'test.pdf',
                'document_type' => 'service_manual',
                'language' => 'de',
                'status' => 'uploaded',
            ], 200),
        ]);

        $file = UploadedFile::fake()->create('test.pdf', 100, 'application/pdf');
        $service = $this->makeService();
        $result = $service->uploadDocument($file, 'service_manual', 'de');

        $this->assertTrue($result['success']);

        Http::assertSent(function (Request $request) {
            $contentType = implode(',', $request->header('Content-Type'));

            return $request->url() === "{$this->baseUrl}/upload"
                && ! str_contains($contentType, 'application/json');
        });
    }

    #[Test]
    public function get_document_status_reads_from_data_wrapper(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/status" => Http::response([
                'success' => true,
                'data' => [
                    'document_id' => 'doc-123',
                    'status' => 'completed',
                    'current_stage' => null,
                    'progress' => 1.0,
                    'queue_position' => 0,
                    'total_queue_items' => 0,
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->getDocumentStatus('doc-123');

        $this->assertTrue($result['success']);
        $this->assertSame('completed', $result['status']);
        $this->assertArrayNotHasKey('document_status', $result);
    }

    #[Test]
    public function get_stage_status_reads_from_data_wrapper_and_has_found_flag(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/stages" => Http::response([
                'success' => true,
                'data' => [
                    'document_id' => 'doc-123',
                    'stage_status' => ['text_extraction' => 'completed'],
                    'found' => true,
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->getStageStatus('doc-123');

        $this->assertTrue($result['success']);
        $this->assertTrue($result['found']);
        $this->assertSame('completed', $result['stage_status']['text_extraction']);
    }

    #[Test]
    public function get_available_stages_calls_global_endpoint_without_document_id(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/stages/names" => Http::response([
                'success' => true,
                'data' => [
                    'stages' => ['text_extraction', 'embedding'],
                    'total' => 2,
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->getAvailableStages();

        $this->assertTrue($result['success']);
        $this->assertSame(['text_extraction', 'embedding'], $result['stages']);

        Http::assertSent(fn (Request $request) => $request->url() === "{$this->baseUrl}/api/v1/stages/names");
    }

    #[Test]
    public function reprocess_document_reads_from_data_wrapper(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/reprocess" => Http::response([
                'success' => true,
                'data' => [
                    'message' => 'Reprocessing queued',
                    'document_id' => 'doc-123',
                    'status' => 'pending',
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->reprocessDocument('doc-123');

        $this->assertTrue($result['success']);
        $this->assertSame('pending', $result['status']);
        $this->assertSame('doc-123', $result['document_id']);
    }

    #[Test]
    public function process_stage_returns_stage_and_document_id_without_processing_time(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/process/stage/embedding" => Http::response([
                'success' => true,
                'data' => [
                    'stage' => 'embedding',
                    'status' => 'queued',
                    'document_id' => 'doc-123',
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->processStage('doc-123', 'embedding');

        $this->assertTrue($result['success']);
        $this->assertSame('embedding', $result['stage']);
        $this->assertSame('doc-123', $result['document_id']);
        $this->assertArrayNotHasKey('processing_time', $result);
    }

    #[Test]
    public function process_multiple_stages_reads_from_data_wrapper_and_sends_json(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/process/stages" => Http::response([
                'success' => true,
                'data' => [
                    'total_stages' => 1,
                    'successful' => 1,
                    'failed' => 0,
                    'success_rate' => 1.0,
                    'stage_results' => [],
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->processMultipleStages('doc-123', ['embedding']);

        $this->assertTrue($result['success']);
        $this->assertSame(1, $result['total_stages']);
        $this->assertSame(1.0, $result['success_rate']);

        Http::assertSent(function (Request $request) {
            $contentType = implode(',', $request->header('Content-Type'));

            return $request->url() === "{$this->baseUrl}/api/v1/documents/doc-123/process/stages"
                && str_contains($contentType, 'application/json')
                && $request['stages'] === ['embedding']
                && $request['stop_on_error'] === true;
        });
    }

    #[Test]
    public function process_video_reads_from_data_wrapper_and_sends_json(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/process/video" => Http::response([
                'success' => true,
                'data' => [
                    'video_id' => 'vid-1',
                    'title' => 'Test',
                    'platform' => 'youtube',
                    'thumbnail_url' => 'https://img.test/thumb.png',
                    'duration' => 120,
                    'channel_title' => 'Chan',
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->processVideo('doc-123', 'https://youtube.com/watch?v=abc');

        $this->assertTrue($result['success']);
        $this->assertSame('youtube', $result['platform']);

        Http::assertSent(function (Request $request) {
            $contentType = implode(',', $request->header('Content-Type'));

            return $request->url() === "{$this->baseUrl}/api/v1/documents/doc-123/process/video"
                && str_contains($contentType, 'application/json')
                && $request['video_url'] === 'https://youtube.com/watch?v=abc';
        });
    }

    #[Test]
    public function generate_thumbnail_reads_from_data_wrapper_and_sends_json(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/process/thumbnail" => Http::response([
                'success' => true,
                'data' => [
                    'thumbnail_url' => 'https://minio.test/thumb.png',
                    'size' => [300, 400],
                    'file_size' => 42000,
                ],
            ], 200),
        ]);

        $service = $this->makeService();
        $result = $service->generateThumbnail('doc-123', [300, 400], 0);

        $this->assertTrue($result['success']);
        $this->assertSame('https://minio.test/thumb.png', $result['thumbnail_url']);
        $this->assertSame([300, 400], $result['size']);

        Http::assertSent(function (Request $request) {
            $contentType = implode(',', $request->header('Content-Type'));

            return $request->url() === "{$this->baseUrl}/api/v1/documents/doc-123/process/thumbnail"
                && str_contains($contentType, 'application/json')
                && $request['size'] === [300, 400]
                && $request['page'] === 0;
        });
    }

    #[Test]
    public function app_service_provider_passes_upload_timeout_from_config(): void
    {
        config([
            'krai.engine_url' => $this->baseUrl,
            'krai.service_jwt' => 'test-token',
            'krai.upload_timeout' => 777,
        ]);

        $this->app->forgetInstance(KraiEngineService::class);

        $service = app(KraiEngineService::class);
        $reflection = new \ReflectionProperty($service, 'uploadTimeout');

        $this->assertSame(777, $reflection->getValue($service));
    }

    #[Test]
    public function upload_timeout_config_default_is_available(): void
    {
        $this->assertSame(600, config('krai.upload_timeout'));
    }
}

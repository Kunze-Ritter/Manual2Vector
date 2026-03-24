<?php

namespace Tests\Feature;

use App\Services\BackendApiService;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class BackendApiServiceTest extends TestCase
{
    protected string $baseUrl = 'http://127.0.0.1:8000';

    /** @test */
    public function retry_stage_uses_document_retry_endpoint_with_normalized_stage_name(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/stages/link_extraction/retry" => Http::response([
                'data' => ['message' => 'retry triggered'],
            ], 200),
        ]);

        $service = app(BackendApiService::class);
        $result = $service->retryStage('doc-123', 'link_extraction_processor');

        $this->assertTrue($result['success']);
        $this->assertSame('retry triggered', $result['data']['message']);

        Http::assertSent(function ($request): bool {
            return $request->method() === 'POST'
                && $request->url() === "{$this->baseUrl}/api/v1/documents/doc-123/stages/link_extraction/retry";
        });
    }

    /** @test */
    public function retry_stage_returns_clear_error_for_unsupported_stages_without_calling_backend(): void
    {
        Http::fake();

        $service = app(BackendApiService::class);
        $result = $service->retryStage('doc-123', 'video_enrichment_processor');

        $this->assertFalse($result['success']);
        $this->assertStringContainsString('Retry is not supported', $result['error']);

        Http::assertNothingSent();
    }

    /** @test */
    public function retry_stage_flattens_nested_backend_error_details(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/documents/doc-123/stages/parts_extraction/retry" => Http::response([
                'detail' => [
                    'error' => 'Stage not failed',
                    'details' => 'Current document stage status is pending',
                ],
            ], 400),
        ]);

        $service = app(BackendApiService::class);
        $result = $service->retryStage('doc-123', 'parts_processor');

        $this->assertFalse($result['success']);
        $this->assertSame(
            'Stage not failed: Current document stage status is pending',
            $result['error']
        );
    }

    /** @test */
    public function mark_error_resolved_flattens_nested_backend_error_details(): void
    {
        Http::fake([
            "{$this->baseUrl}/api/v1/pipeline/mark-error-resolved" => Http::response([
                'detail' => [
                    'error' => 'Error not found',
                    'details' => 'No error found with ID: err_missing',
                ],
            ], 404),
        ]);

        $service = app(BackendApiService::class);
        $result = $service->markErrorResolved('err_missing', 'user-1', 'done');

        $this->assertFalse($result['success']);
        $this->assertSame(
            'Error not found: No error found with ID: err_missing',
            $result['error']
        );
    }
}

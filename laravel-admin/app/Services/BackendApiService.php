<?php

namespace App\Services;

use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * BackendApiService - Laravel service for communicating with FastAPI backend
 *
 * Provides methods to interact with FastAPI pipeline error management endpoints:
 * - GET /api/v1/pipeline/errors - Fetch pipeline errors with filters
 * - POST /api/v1/pipeline/retry-stage - Retry a failed pipeline stage
 * - POST /api/v1/pipeline/mark-error-resolved - Mark an error as resolved
 *
 * Uses JWT authentication via TokenService.
 */
class BackendApiService
{
    private TokenService $tokenService;

    /**
     * Create a new BackendApiService instance
     *
     * @param  string|null  $baseUrl  Base URL for FastAPI backend (default: config('krai.engine_url'))
     * @param  string|null  $serviceJwt  Service JWT token (default: config('krai.service_jwt'))
     */
    public function __construct(
        private ?string $baseUrl = null,
        private ?string $serviceJwt = null,
    ) {
        $this->baseUrl = rtrim($baseUrl ?? config('krai.engine_url', 'http://krai-engine:8000'), '/');
        $this->serviceJwt = $serviceJwt ?? config('krai.service_jwt');
        $this->tokenService = new TokenService($this->baseUrl, $this->serviceJwt);
    }

    /**
     * Retry a failed pipeline stage for a document
     *
     * Calls the document stage retry endpoint for canonical retryable stages.
     *
     * @param  string  $documentId  The document ID to retry
     * @param  string  $stageName  The pipeline stage name to retry
     * @return array Response array with keys: success (bool), data (array), error (string|null)
     *
     * @example
     * $result = $service->retryStage('doc-123', 'classification');
     * if ($result['success']) {
     *     // Stage retry initiated successfully
     *     $data = $result['data'];
     * } else {
     *     // Handle error
     *     $errorMessage = $result['error'];
     * }
     */
    public function retryStage(string $documentId, string $stageName): array
    {
        $normalizedStageName = $this->normalizeRetryStageName($stageName);

        if ($normalizedStageName === null) {
            return [
                'success' => false,
                'data' => [],
                'error' => "Retry is not supported for stage '{$stageName}' from the admin UI.",
            ];
        }

        try {
            $endpoint = "{$this->baseUrl}/api/v1/documents/{$documentId}/stages/{$normalizedStageName}/retry";
            $client = $this->createHttpClient();

            $response = $client->post($endpoint);

            if ($response->successful()) {
                $data = $response->json('data', []);

                return [
                    'success' => true,
                    'data' => $data,
                    'error' => null,
                ];
            }

            $errorMessage = $this->extractErrorMessage($response);
            Log::error('BackendApiService::retryStage failed', [
                'document_id' => $documentId,
                'stage_name' => $stageName,
                'normalized_stage_name' => $normalizedStageName,
                'status_code' => $response->status(),
                'error' => $errorMessage,
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => $errorMessage,
            ];
        } catch (\Illuminate\Http\Client\ConnectionException $e) {
            Log::error('BackendApiService::retryStage connection error', [
                'document_id' => $documentId,
                'stage_name' => $stageName,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        } catch (\Illuminate\Http\Client\RequestException $e) {
            Log::error('BackendApiService::retryStage request error', [
                'document_id' => $documentId,
                'stage_name' => $stageName,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        } catch (\Exception $e) {
            Log::error('BackendApiService::retryStage unexpected error', [
                'document_id' => $documentId,
                'stage_name' => $stageName,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        }
    }

    /**
     * Mark a pipeline error as resolved
     *
     * Calls POST /api/v1/pipeline/mark-error-resolved to mark an error as resolved.
     *
     * @param  string  $errorId  The error ID to mark as resolved
     * @param  string|null  $userId  Optional user ID who resolved the error
     * @param  string|null  $notes  Optional resolution notes
     * @return array Response array with keys: success (bool), data (array), error (string|null)
     *
     * @example
     * $result = $service->markErrorResolved('error-456', 'user-789', 'Fixed by reprocessing');
     * if ($result['success']) {
     *     // Error marked as resolved
     *     $data = $result['data'];
     * } else {
     *     // Handle error
     *     $errorMessage = $result['error'];
     * }
     */
    public function markErrorResolved(string $errorId, ?string $userId = null, ?string $notes = null): array
    {
        try {
            $endpoint = "{$this->baseUrl}/api/v1/pipeline/mark-error-resolved";
            $client = $this->createHttpClient();

            $response = $client->post($endpoint, [
                'error_id' => $errorId,
                'user_id' => $userId,
                'notes' => $notes,
            ]);

            if ($response->successful()) {
                $data = $response->json('data', []);

                return [
                    'success' => true,
                    'data' => $data,
                    'error' => null,
                ];
            }

            $errorMessage = $this->extractErrorMessage($response);
            Log::error('BackendApiService::markErrorResolved failed', [
                'error_id' => $errorId,
                'user_id' => $userId,
                'status_code' => $response->status(),
                'error' => $errorMessage,
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => $errorMessage,
            ];
        } catch (\Illuminate\Http\Client\ConnectionException $e) {
            Log::error('BackendApiService::markErrorResolved connection error', [
                'error_id' => $errorId,
                'user_id' => $userId,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        } catch (\Illuminate\Http\Client\RequestException $e) {
            Log::error('BackendApiService::markErrorResolved request error', [
                'error_id' => $errorId,
                'user_id' => $userId,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        } catch (\Exception $e) {
            Log::error('BackendApiService::markErrorResolved unexpected error', [
                'error_id' => $errorId,
                'user_id' => $userId,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        }
    }

    /**
     * Get pipeline errors with optional filters
     *
     * Calls GET /api/v1/pipeline/errors to fetch error records.
     *
     * @param  array  $filters  Optional filters for the query
     *                          Supported keys: document_id, stage_name, error_type, status,
     *                          date_from, date_to, page, page_size
     * @return array Response array with keys: success (bool), data (array), error (string|null)
     *
     * @example
     * $result = $service->getErrors([
     *     'stage_name' => 'classification',
     *     'status' => 'unresolved',
     *     'page' => 1,
     *     'page_size' => 50
     * ]);
     * if ($result['success']) {
     *     $errors = $result['data'];
     * } else {
     *     $errorMessage = $result['error'];
     * }
     */
    public function getErrors(array $filters = []): array
    {
        try {
            $endpoint = "{$this->baseUrl}/api/v1/pipeline/errors";
            $client = $this->createHttpClient();

            $queryParams = [];
            foreach ($filters as $key => $value) {
                if ($value !== null) {
                    if ($value instanceof \DateTime || $value instanceof \DateTimeInterface) {
                        $queryParams[$key] = $value->format('c');
                    } else {
                        $queryParams[$key] = $value;
                    }
                }
            }

            $response = $client->get($endpoint, $queryParams);

            if ($response->successful()) {
                $data = $response->json('data', []);

                return [
                    'success' => true,
                    'data' => $data,
                    'error' => null,
                ];
            }

            $errorMessage = $this->extractErrorMessage($response);
            Log::error('BackendApiService::getErrors failed', [
                'filters' => $filters,
                'status_code' => $response->status(),
                'error' => $errorMessage,
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => $errorMessage,
            ];
        } catch (\Illuminate\Http\Client\ConnectionException $e) {
            Log::error('BackendApiService::getErrors connection error', [
                'filters' => $filters,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        } catch (\Illuminate\Http\Client\RequestException $e) {
            Log::error('BackendApiService::getErrors request error', [
                'filters' => $filters,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        } catch (\Exception $e) {
            Log::error('BackendApiService::getErrors unexpected error', [
                'filters' => $filters,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return [
                'success' => false,
                'data' => [],
                'error' => 'Connection error: '.$e->getMessage(),
            ];
        }
    }

    /**
     * Validate service configuration
     *
     * Checks if required configuration values are set.
     *
     * @return bool True if configuration is valid, false otherwise
     */
    public function validateConfiguration(): bool
    {
        $isValid = true;

        if (empty($this->baseUrl)) {
            Log::warning('BackendApiService: engine_url is not configured');
            $isValid = false;
        }

        $hasJwt = ! empty($this->serviceJwt);
        $hasCredentials = ! empty(env('KRAI_ENGINE_ADMIN_USERNAME')) && ! empty(env('KRAI_ENGINE_ADMIN_PASSWORD'));

        if (! $hasJwt && ! $hasCredentials) {
            Log::warning('BackendApiService: Neither service_jwt nor admin credentials are configured');
            $isValid = false;
        }

        return $isValid;
    }

    public function isRetrySupportedStage(string $stageName): bool
    {
        return $this->normalizeRetryStageName($stageName) !== null;
    }

    public function normalizeRetryStageName(string $stageName): ?string
    {
        $normalizedStageName = strtolower(trim($stageName));
        $canonicalStages = array_keys(config('krai.stages', []));

        if (in_array($normalizedStageName, $canonicalStages, true)) {
            return $normalizedStageName;
        }

        return [
            'upload_processor' => 'upload',
            'text_processor' => 'text_extraction',
            'tableprocessor' => 'table_extraction',
            'table_processor' => 'table_extraction',
            'svg_processor' => 'svg_processing',
            'image_processor' => 'image_processing',
            'visualembeddingprocessor' => 'visual_embedding',
            'visual_embedding_processor' => 'visual_embedding',
            'link_extraction_processor' => 'link_extraction',
            'chunk_preprocessor' => 'chunk_prep',
            'classification_processor' => 'classification',
            'metadata_processor_ai' => 'metadata_extraction',
            'parts_processor' => 'parts_extraction',
            'series_processor' => 'series_detection',
            'series_detection_processor' => 'series_detection',
            'storage_processor' => 'storage',
            'embedding_processor' => 'embedding',
            'search_processor' => 'search_indexing',
        ][$normalizedStageName] ?? null;
    }

    /**
     * Create HTTP client with proper headers and timeout
     *
     * @return \Illuminate\Http\Client\PendingRequest
     */
    private function createHttpClient()
    {
        return Http::timeout(config('krai.default_timeout', 10))->withHeaders($this->buildHeaders());
    }

    private function extractErrorMessage(Response $response): string
    {
        $detail = $response->json('detail');

        if (is_string($detail) && $detail !== '') {
            return $detail;
        }

        if (is_array($detail)) {
            $error = $detail['error'] ?? null;
            $details = $detail['details'] ?? null;

            $parts = array_filter([
                is_string($error) && $error !== '' ? $error : null,
                is_string($details) && $details !== '' ? $details : null,
            ]);

            if ($parts !== []) {
                return implode(': ', $parts);
            }

            return json_encode($detail, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) ?: 'Unknown backend error';
        }

        $body = trim($response->body());

        if ($body !== '') {
            return $body;
        }

        return "HTTP {$response->status()}";
    }

    /**
     * Build HTTP headers including authentication
     */
    private function buildHeaders(): array
    {
        $headers = [
            'Accept' => 'application/json',
            'Content-Type' => 'application/json',
        ];

        $token = $this->tokenService->getToken();
        if ($token) {
            $headers['Authorization'] = "Bearer {$token}";
        }

        return $headers;
    }
}

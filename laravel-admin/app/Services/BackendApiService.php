<?php

namespace App\Services;

use Illuminate\Support\Facades\Cache;
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
 * Uses JWT authentication with automatic token caching and refresh.
 */
class BackendApiService
{
    private string $baseUrl;
    private ?string $serviceJwt;

    /**
     * Create a new BackendApiService instance
     * 
     * @param string|null $baseUrl Base URL for FastAPI backend (default: config('krai.engine_url'))
     * @param string|null $serviceJwt Service JWT token (default: config('krai.service_jwt'))
     */
    public function __construct(?string $baseUrl = null, ?string $serviceJwt = null)
    {
        $this->baseUrl = rtrim($baseUrl ?? config('krai.engine_url', 'http://krai-engine:8000'), '/');
        $this->serviceJwt = $serviceJwt ?? config('krai.service_jwt');
    }

    /**
     * Retry a failed pipeline stage for a document
     * 
     * Calls POST /api/v1/pipeline/retry-stage to reprocess a specific stage.
     * 
     * @param string $documentId The document ID to retry
     * @param string $stageName The pipeline stage name to retry
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
        try {
            $endpoint = "{$this->baseUrl}/api/v1/pipeline/retry-stage";
            $client = $this->createHttpClient();
            
            $response = $client->post($endpoint, [
                'document_id' => $documentId,
                'stage_name' => $stageName,
            ]);

            if ($response->successful()) {
                $data = $response->json('data', []);
                return [
                    'success' => true,
                    'data' => $data,
                    'error' => null,
                ];
            }

            $errorMessage = $response->json('detail') ?? $response->body();
            Log::error('BackendApiService::retryStage failed', [
                'document_id' => $documentId,
                'stage_name' => $stageName,
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
                'error' => 'Connection error: ' . $e->getMessage(),
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
                'error' => 'Connection error: ' . $e->getMessage(),
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
                'error' => 'Connection error: ' . $e->getMessage(),
            ];
        }
    }

    /**
     * Mark a pipeline error as resolved
     * 
     * Calls POST /api/v1/pipeline/mark-error-resolved to mark an error as resolved.
     * 
     * @param string $errorId The error ID to mark as resolved
     * @param string|null $userId Optional user ID who resolved the error
     * @param string|null $notes Optional resolution notes
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

            $errorMessage = $response->json('detail') ?? $response->body();
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
                'error' => 'Connection error: ' . $e->getMessage(),
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
                'error' => 'Connection error: ' . $e->getMessage(),
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
                'error' => 'Connection error: ' . $e->getMessage(),
            ];
        }
    }

    /**
     * Get pipeline errors with optional filters
     * 
     * Calls GET /api/v1/pipeline/errors to fetch error records.
     * 
     * @param array $filters Optional filters for the query
     *                       Supported keys: document_id, stage_name, error_type, status,
     *                       date_from, date_to, page, page_size
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

            $errorMessage = $response->json('detail') ?? $response->body();
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
                'error' => 'Connection error: ' . $e->getMessage(),
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
                'error' => 'Connection error: ' . $e->getMessage(),
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
                'error' => 'Connection error: ' . $e->getMessage(),
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

        $hasJwt = !empty($this->serviceJwt);
        $hasCredentials = !empty(env('KRAI_ENGINE_ADMIN_USERNAME')) && !empty(env('KRAI_ENGINE_ADMIN_PASSWORD'));

        if (!$hasJwt && !$hasCredentials) {
            Log::warning('BackendApiService: Neither service_jwt nor admin credentials are configured');
            $isValid = false;
        }

        return $isValid;
    }

    /**
     * Create HTTP client with proper headers and timeout
     * 
     * @return \Illuminate\Http\Client\PendingRequest
     */
    private function createHttpClient()
    {
        return Http::timeout(10)->withHeaders($this->buildHeaders());
    }

    /**
     * Build HTTP headers including authentication
     * 
     * @return array
     */
    private function buildHeaders(): array
    {
        $headers = [
            'Accept' => 'application/json',
            'Content-Type' => 'application/json',
        ];

        $token = $this->getOrCreateServiceJwt();
        if ($token) {
            $headers['Authorization'] = "Bearer {$token}";
        }

        return $headers;
    }

    /**
     * Get or create service JWT token with caching
     * 
     * Attempts to retrieve cached token or perform auto-login to obtain new token.
     * Tokens are cached for 55 minutes.
     * 
     * @return string|null JWT token or null on failure
     */
    private function getOrCreateServiceJwt(): ?string
    {
        if ($this->serviceJwt) {
            return $this->serviceJwt;
        }

        $cacheKey = 'krai.service_jwt.cached';
        $cachedToken = Cache::get($cacheKey);
        
        if ($cachedToken) {
            return $cachedToken;
        }

        $username = env('KRAI_ENGINE_ADMIN_USERNAME');
        $password = env('KRAI_ENGINE_ADMIN_PASSWORD');

        if (empty($username) || empty($password)) {
            Log::warning('BackendApiService: Cannot auto-login, credentials not configured');
            return null;
        }

        try {
            $response = Http::timeout(10)->post("{$this->baseUrl}/api/v1/auth/login", [
                'username' => $username,
                'password' => $password,
            ]);

            if ($response->successful()) {
                $token = $response->json('data.access_token');
                
                if ($token) {
                    Cache::put($cacheKey, $token, now()->addMinutes(55));
                    return $token;
                }
            }

            Log::warning('BackendApiService: Auto-login failed', [
                'status_code' => $response->status(),
                'error' => $response->json('detail') ?? $response->body(),
            ]);
        } catch (\Exception $e) {
            Log::warning('BackendApiService: Auto-login exception', [
                'message' => $e->getMessage(),
            ]);
        }

        return null;
    }
}

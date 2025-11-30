<?php

namespace App\Services;

use Illuminate\Http\Client\PendingRequest;
use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use App\Models\User;

class KraiEngineService
{
    private string $baseUrl;
    private string $serviceToken;
    private int $defaultTimeout;
    private int $queryTimeout;

    public function __construct(string $baseUrl, string $serviceToken, int $defaultTimeout = 120, int $queryTimeout = 60)
    {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->serviceToken = $serviceToken;
        $this->defaultTimeout = $defaultTimeout;
        $this->queryTimeout = $queryTimeout;
    }

    /**
     * Create HTTP client with default headers
     */
    private function createHttpClient(int $timeout = null): PendingRequest
    {
        $client = Http::timeout($timeout ?? $this->defaultTimeout)
            ->withHeaders([
                'Content-Type' => 'application/json',
                'Accept' => 'application/json',
            ]);

        if ($this->serviceToken) {
            $client->withHeaders([
                'Authorization' => 'Bearer ' . $this->serviceToken,
            ]);
        }

        return $client;
    }

    /**
     * Add user context headers to HTTP client
     */
    private function addUserContext(PendingRequest $client, ?User $user = null): PendingRequest
    {
        if (!$user) {
            $user = auth()->user();
        }

        if ($user) {
            $client->withHeaders([
                'X-Uploader-Username' => $user->name ?? null,
                'X-Uploader-UserId' => (string) ($user->id ?? ''),
                'X-Uploader-Source' => 'laravel-admin',
            ]);
        }

        return $client;
    }

    /**
     * Log API call with context
     */
    private function logApiCall(string $method, string $endpoint, string $documentId, int $status, ?string $error = null): void
    {
        $message = sprintf(
            'KRAI Engine API: %s %s - Document: %s - Status: %d',
            $method,
            $endpoint,
            $documentId,
            $status
        );

        if ($error) {
            $message .= ' - Error: ' . $error;
        }

        if ($status >= 400) {
            Log::channel('krai-engine')->error($message);
        } else {
            Log::channel('krai-engine')->info($message);
        }
    }

    /**
     * Process a single stage for a document
     */
    public function processStage(string $documentId, string $stageName, ?User $user = null): array
    {
        $endpoint = "/documents/{$documentId}/process/stage/{$stageName}";
        
        try {
            $client = $this->createHttpClient();
            $client = $this->addUserContext($client, $user);
            
            $response = $client->post($this->baseUrl . $endpoint);
            
            $this->logApiCall('POST', $endpoint, $documentId, $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'stage' => $stageName,
                    'data' => $data,
                    'processing_time' => $data['processing_time'] ?? 0,
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('POST', $endpoint, $documentId, $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('POST', $endpoint, $documentId, 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
            ];
        }
    }

    /**
     * Process multiple stages for a document
     */
    public function processMultipleStages(string $documentId, array $stages, bool $stopOnError = true, ?User $user = null): array
    {
        $endpoint = "/documents/{$documentId}/process/stages";
        
        try {
            $client = $this->createHttpClient();
            $client = $this->addUserContext($client, $user);
            
            $payload = [
                'stages' => $stages,
                'stop_on_error' => $stopOnError,
            ];
            
            $response = $client->post($this->baseUrl . $endpoint, $payload);
            
            $this->logApiCall('POST', $endpoint, $documentId, $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'total_stages' => $data['total_stages'] ?? count($stages),
                    'successful' => $data['successful'] ?? 0,
                    'failed' => $data['failed'] ?? 0,
                    'stage_results' => $data['stage_results'] ?? [],
                    'success_rate' => $data['success_rate'] ?? 0,
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('POST', $endpoint, $documentId, $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                    'total_stages' => count($stages),
                    'successful' => 0,
                    'failed' => count($stages),
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('POST', $endpoint, $documentId, 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
                'total_stages' => count($stages),
                'successful' => 0,
                'failed' => count($stages),
            ];
        }
    }

    /**
     * Process video enrichment for a document
     */
    public function processVideo(string $documentId, string $videoUrl, ?string $manufacturerId = null, ?User $user = null): array
    {
        $endpoint = "/documents/{$documentId}/process/video";
        
        try {
            $client = $this->createHttpClient();
            $client = $this->addUserContext($client, $user);
            
            $payload = [
                'video_url' => $videoUrl,
            ];
            
            if ($manufacturerId) {
                $payload['manufacturer_id'] = $manufacturerId;
            }
            
            $response = $client->post($this->baseUrl . $endpoint, $payload);
            
            $this->logApiCall('POST', $endpoint, $documentId, $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'video_id' => $data['video_id'] ?? null,
                    'title' => $data['title'] ?? null,
                    'platform' => $data['platform'] ?? null,
                    'thumbnail_url' => $data['thumbnail_url'] ?? null,
                    'duration' => $data['duration'] ?? null,
                    'channel_title' => $data['channel_title'] ?? null,
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('POST', $endpoint, $documentId, $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('POST', $endpoint, $documentId, 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
            ];
        }
    }

    /**
     * Generate thumbnail for a document
     */
    public function generateThumbnail(string $documentId, array $size = [300, 400], int $page = 0, ?User $user = null): array
    {
        $endpoint = "/documents/{$documentId}/process/thumbnail";
        
        try {
            $client = $this->createHttpClient();
            $client = $this->addUserContext($client, $user);
            
            $payload = [
                'size' => $size,
                'page' => $page,
            ];
            
            $response = $client->post($this->baseUrl . $endpoint, $payload);
            
            $this->logApiCall('POST', $endpoint, $documentId, $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'thumbnail_url' => $data['thumbnail_url'] ?? null,
                    'size' => $data['size'] ?? $size,
                    'file_size' => $data['file_size'] ?? null,
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('POST', $endpoint, $documentId, $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('POST', $endpoint, $documentId, 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
            ];
        }
    }

    /**
     * Get stage status for a document
     */
    public function getStageStatus(string $documentId): array
    {
        $endpoint = "/documents/{$documentId}/stages/status";
        
        try {
            $client = $this->createHttpClient($this->queryTimeout);
            
            $response = $client->get($this->baseUrl . $endpoint);
            
            $this->logApiCall('GET', $endpoint, $documentId, $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'document_id' => $data['document_id'] ?? $documentId,
                    'stage_status' => $data['stage_status'] ?? [],
                    'found' => true,
                ];
            } elseif ($response->status() === 404) {
                return [
                    'success' => true,
                    'document_id' => $documentId,
                    'stage_status' => [],
                    'found' => false,
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('GET', $endpoint, $documentId, $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                    'found' => false,
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('GET', $endpoint, $documentId, 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
                'found' => false,
            ];
        }
    }

    /**
     * Get available stages for a document
     */
    public function getAvailableStages(string $documentId): array
    {
        $endpoint = "/documents/{$documentId}/stages";
        
        try {
            $client = $this->createHttpClient($this->queryTimeout);
            
            $response = $client->get($this->baseUrl . $endpoint);
            
            $this->logApiCall('GET', $endpoint, $documentId, $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'stages' => $data['stages'] ?? [],
                    'total' => $data['total'] ?? 0,
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('GET', $endpoint, $documentId, $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                    'stages' => [],
                    'total' => 0,
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('GET', $endpoint, $documentId, 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
                'stages' => [],
                'total' => 0,
            ];
        }
    }

    /**
     * Get document processing status
     */
    public function getDocumentStatus(string $documentId): array
    {
        $endpoint = "/documents/{$documentId}/status";
        
        try {
            $client = $this->createHttpClient($this->queryTimeout);
            
            $response = $client->get($this->baseUrl . $endpoint);
            
            $this->logApiCall('GET', $endpoint, $documentId, $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'document_status' => $data['document_status'] ?? 'unknown',
                    'queue_position' => $data['queue_position'] ?? 0,
                    'total_queue_items' => $data['total_queue_items'] ?? 0,
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('GET', $endpoint, $documentId, $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('GET', $endpoint, $documentId, 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
            ];
        }
    }

    /**
     * Upload a document to the KRAI Engine
     */
    public function uploadDocument(\Illuminate\Http\UploadedFile $file, string $documentType, string $language = 'en', ?User $user = null): array
    {
        $endpoint = "/documents/upload";
        
        try {
            $client = $this->createHttpClient();
            $client = $this->addUserContext($client, $user);
            
            $response = $client->attach(
                'file',
                fopen($file->getRealPath(), 'rb'),
                $file->getClientOriginalName()
            )->post($this->baseUrl . $endpoint, [
                'document_type' => $documentType,
                'language' => $language,
            ]);
            
            $this->logApiCall('POST', $endpoint, 'upload', $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'document_id' => $data['document_id'] ?? null,
                    'filename' => $data['filename'] ?? $file->getClientOriginalName(),
                    'document_type' => $data['document_type'] ?? $documentType,
                    'language' => $data['language'] ?? $language,
                    'status' => $data['status'] ?? 'uploaded',
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('POST', $endpoint, 'upload', $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('POST', $endpoint, 'upload', 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
            ];
        }
    }

    /**
     * Reprocess a document (full pipeline)
     */
    public function reprocessDocument(string $documentId, ?User $user = null): array
    {
        $endpoint = "/documents/{$documentId}/reprocess";
        
        try {
            $client = $this->createHttpClient();
            $client = $this->addUserContext($client, $user);
            
            $response = $client->post($this->baseUrl . $endpoint);
            
            $this->logApiCall('POST', $endpoint, $documentId, $response->status());
            
            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'message' => $data['message'] ?? 'Document reprocessing started',
                    'document_id' => $data['document_id'] ?? $documentId,
                    'status' => $data['status'] ?? 'started',
                ];
            } else {
                $error = $response->json('detail', 'Unknown error');
                $this->logApiCall('POST', $endpoint, $documentId, $response->status(), $error);
                return [
                    'success' => false,
                    'error' => $error,
                ];
            }
        } catch (\Exception $e) {
            $this->logApiCall('POST', $endpoint, $documentId, 500, $e->getMessage());
            return [
                'success' => false,
                'error' => 'Connection error: ' . $e->getMessage(),
            ];
        }
    }
}

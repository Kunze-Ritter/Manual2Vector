<?php

namespace App\Services;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\PendingRequest;
use Illuminate\Http\Client\RequestException;
use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use JsonException;
use Symfony\Component\HttpFoundation\StreamedResponse;

class AiAgentService
{
    private string $baseUrl;
    private ?string $serviceJwt;
    private array $timeouts;
    private array $cacheTtl;
    private array $sessionConfig;

    public function __construct(?string $baseUrl = null, ?string $serviceJwt = null)
    {
        $this->baseUrl = rtrim($baseUrl ?? config('krai.ai_agent.base_url'), '/');
        $this->serviceJwt = $serviceJwt ?? config('krai.service_jwt');
        $this->timeouts = config('krai.ai_agent.timeout', []);
        $this->cacheTtl = config('krai.ai_agent.cache_ttl', []);
        $this->sessionConfig = config('krai.ai_agent.session', []);
    }

    private function createHttpClient(?int $timeout = null): PendingRequest
    {
        $client = Http::timeout($timeout ?? $this->timeouts['chat'] ?? 60)
            ->withHeaders([
                'Content-Type' => 'application/json',
                'Accept' => 'application/json',
            ]);

        if ($this->serviceJwt) {
            $client->withHeaders([
                'Authorization' => 'Bearer ' . $this->serviceJwt,
            ]);
        }

        return $client;
    }

    private function logApiCall(string $method, string $endpoint, string $sessionId, int $status, ?string $error = null): void
    {
        $message = sprintf(
            'AI Agent API: %s %s - Session: %s - Status: %d',
            $method,
            $endpoint,
            $sessionId,
            $status
        );

        if ($error) {
            $message .= ' - Error: ' . $error;
        }

        if ($status >= 400) {
            Log::channel('ai-agent')->error($message);
        } else {
            Log::channel('ai-agent')->info($message);
        }
    }

    public function generateSessionId(?string $userId = null): string
    {
        $prefix = $this->sessionConfig['default_session_prefix'] ?? 'krai_chat_';
        $suffix = $userId ?? uniqid();

        return $prefix . $suffix . '_' . time();
    }

    public function getSessionHistory(string $sessionId): array
    {
        $cacheKey = "ai_agent.session.{$sessionId}";

        return Cache::get($cacheKey, []);
    }

    public function saveSessionHistory(string $sessionId, array $history): void
    {
        $cacheKey = "ai_agent.session.{$sessionId}";
        $ttl = $this->cacheTtl['session_history'] ?? 3600;
        $maxLength = $this->sessionConfig['max_history_length'] ?? 50;

        if (count($history) > $maxLength) {
            $history = array_slice($history, -$maxLength);
        }

        Cache::put($cacheKey, $history, $ttl);
    }

    public function clearSessionHistory(string $sessionId): void
    {
        $cacheKey = "ai_agent.session.{$sessionId}";
        Cache::forget($cacheKey);
    }

    /**
     * Chat with AI agent.
     *
     * @return array{
     *     success: bool,
     *     data?: array{response: string, session_id: string, timestamp: string},
     *     error: ?string
     * }
     */
    public function chat(string $message, string $sessionId): array
    {
        $endpoint = '/chat';

        try {
            $client = $this->createHttpClient($this->timeouts['chat'] ?? 60);

            $payload = [
                'message' => $message,
                'session_id' => $sessionId,
                'stream' => false,
            ];

            /** @var Response $response */
            $response = $client->post($this->baseUrl . $endpoint, $payload);

            $this->logApiCall('POST', $endpoint, $sessionId, $response->status());

            if ($response->successful()) {
                $data = $response->json();

                return [
                    'success' => true,
                    'data' => [
                        'response' => $data['response'] ?? '',
                        'session_id' => $data['session_id'] ?? $sessionId,
                        'timestamp' => $data['timestamp'] ?? now()->toIso8601String(),
                    ],
                    'error' => null,
                ];
            }

            $error = $response->json('detail', 'Unknown error');
            $this->logApiCall('POST', $endpoint, $sessionId, $response->status(), $error);

            return [
                'success' => false,
                'data' => [
                    'response' => '',
                    'session_id' => $sessionId,
                    'timestamp' => now()->toIso8601String(),
                ],
                'error' => $error,
            ];
        } catch (\Exception $e) {
            $errorInfo = $this->classifyConnectionError($e, $this->baseUrl . $endpoint, $this->timeouts['chat'] ?? 60);
            $this->logApiCall('POST', $endpoint, $sessionId, 500, $errorInfo['message']);

            Log::error('AI Agent chat request failed', [
                'error_type' => $errorInfo['type'],
                'message' => $errorInfo['message'],
                'url' => $errorInfo['url'],
                'session_id' => $sessionId,
            ]);

            return [
                'success' => false,
                'data' => [
                    'response' => '',
                    'session_id' => $sessionId,
                    'timestamp' => now()->toIso8601String(),
                ],
                'error' => $errorInfo['message'],
                'error_type' => $errorInfo['type'],
                'attempted_url' => $errorInfo['url'],
            ];
        }
    }

    /**
     * Stream chat response from AI agent (history is persisted after full stream).
     * Note: This replays a buffered SSE response from the backend; it does not stream tokens as they arrive.
     */
    public function chatStream(string $message, string $sessionId): StreamedResponse
    {
        $endpoint = '/chat/stream';

        return new StreamedResponse(function () use ($message, $sessionId, $endpoint) {
            $fullResponse = '';
            $streamComplete = false;

            try {
                $client = $this->createHttpClient($this->timeouts['stream'] ?? 120);

                $payload = [
                    'message' => $message,
                    'session_id' => $sessionId,
                    'stream' => true,
                ];

                /** @var Response $response */
                $response = $client->post($this->baseUrl . $endpoint, $payload);

                if ($response->successful()) {
                    // Backend returns SSE text after completing generation; we replay it to the client.
                    $body = $response->body();
                    $lines = explode("\n", $body);

                    foreach ($lines as $line) {
                        $line = trim($line);

                        if (str_starts_with($line, 'data: ')) {
                            $data = substr($line, 6);

                            if ($data === '[DONE]') {
                                break;
                            }

                            try {
                                $json = json_decode($data, true, 512, JSON_THROW_ON_ERROR);
                                if (isset($json['chunk'])) {
                                    $chunk = $json['chunk'];
                                    $fullResponse .= $chunk;

                                    echo 'data: ' . json_encode(['chunk' => $chunk]) . "\n\n";
                                    if (ob_get_level() > 0) {
                                        ob_flush();
                                    }
                                    flush();
                                }
                            } catch (JsonException $e) {
                                Log::channel('ai-agent')->error('Failed to parse SSE chunk: ' . $e->getMessage());
                            }
                        }
                    }

                    $streamComplete = true;
                    $this->appendExchange($sessionId, $message, $fullResponse, true);

                    $this->logApiCall('POST', $endpoint, $sessionId, 200);
                } else {
                    $error = $response->json('detail', 'Unknown error');
                    $this->logApiCall('POST', $endpoint, $sessionId, $response->status(), $error);

                    echo 'data: ' . json_encode(['error' => $error]) . "\n\n";
                    if (ob_get_level() > 0) {
                        ob_flush();
                    }
                    flush();
                }

                echo "data: [DONE]\n\n";
                if (ob_get_level() > 0) {
                    ob_flush();
                }
                flush();
            } catch (\Exception $e) {
                $errorInfo = $this->classifyConnectionError($e, $this->baseUrl . $endpoint, $this->timeouts['stream'] ?? 120);
                $this->logApiCall('POST', $endpoint, $sessionId, 500, $errorInfo['message']);

                Log::error('AI Agent chat stream failed', [
                    'error_type' => $errorInfo['type'],
                    'message' => $errorInfo['message'],
                    'url' => $errorInfo['url'],
                    'session_id' => $sessionId,
                ]);

                if (!$streamComplete) {
                    $this->appendExchange($sessionId, $message, $fullResponse, false);
                }

                echo 'data: ' . json_encode([
                    'error' => $errorInfo['message'],
                    'error_type' => $errorInfo['type'],
                    'attempted_url' => $errorInfo['url'],
                ]) . "\n\n";
                if (ob_get_level() > 0) {
                    ob_flush();
                }
                flush();
            }
        }, 200, [
            'Content-Type' => 'text/event-stream',
            'Cache-Control' => 'no-cache',
            'X-Accel-Buffering' => 'no',
        ]);
    }

    /**
     * Check AI agent health.
     *
     * @return array{
     *     success: bool,
     *     data?: array{status: string, agent: string, version: string},
     *     error: ?string
     * }
     */
    public function health(): array
    {
        $endpoint = '/health';

        try {
            $client = $this->createHttpClient($this->timeouts['health'] ?? 5);

            /** @var Response $response */
            $response = $client->get($this->baseUrl . $endpoint);

            if ($response->successful()) {
                $data = $response->json();

                return [
                    'success' => true,
                    'data' => [
                        'status' => $data['status'] ?? 'unknown',
                        'agent' => $data['agent'] ?? 'KRAI AI Agent',
                        'version' => $data['version'] ?? '1.0.0',
                    ],
                    'error' => null,
                ];
            }

            return [
                'success' => false,
                'data' => [
                    'status' => 'unhealthy',
                    'agent' => 'KRAI AI Agent',
                    'version' => '1.0.0',
                ],
                'error' => 'HTTP ' . $response->status() . ': ' . $response->body(),
            ];
        } catch (\Exception $e) {
            $errorInfo = $this->classifyConnectionError($e, $this->baseUrl . $endpoint, $this->timeouts['health'] ?? 5);
            
            Log::error('AI Agent health check failed', [
                'error_type' => $errorInfo['type'],
                'message' => $errorInfo['message'],
                'url' => $errorInfo['url'],
            ]);

            return [
                'success' => false,
                'data' => [
                    'status' => 'unreachable',
                    'agent' => 'KRAI AI Agent',
                    'version' => '1.0.0',
                ],
                'error' => $errorInfo['message'],
                'error_type' => $errorInfo['type'],
                'attempted_url' => $errorInfo['url'],
            ];
        }
    }

    /**
     * Classify connection error for detailed error messages.
     */
    private function classifyConnectionError(\Exception $e, string $url, ?int $timeoutSeconds = null): array
    {
        $message = $e->getMessage();
        $hostname = parse_url($url, PHP_URL_HOST) ?? 'unknown';

        // DNS resolution failure
        if (str_contains($message, 'Could not resolve host') || str_contains($message, 'getaddrinfo failed')) {
            return [
                'type' => 'dns',
                'message' => "Service unreachable: DNS resolution failed for {$hostname}",
                'url' => $url,
            ];
        }

        // Connection timeout
        if (str_contains($message, 'timed out') || str_contains($message, 'timeout')) {
            $timeout = $timeoutSeconds ?? $this->timeouts['health'] ?? 5;
            return [
                'type' => 'timeout',
                'message' => "Service unreachable: Connection timeout after {$timeout}s",
                'url' => $url,
            ];
        }

        // Connection refused
        if (str_contains($message, 'Connection refused') || str_contains($message, 'Failed to connect')) {
            return [
                'type' => 'refused',
                'message' => "Service unreachable: Connection refused (service may be down)",
                'url' => $url,
            ];
        }

        // Generic connection error
        return [
            'type' => 'connection',
            'message' => "Connection error: {$message}",
            'url' => $url,
        ];
    }

    public function appendExchange(string $sessionId, string $userMessage, string $assistantMessage, bool $complete = true): void
    {
        $history = $this->getSessionHistory($sessionId);
        $history[] = [
            'role' => 'user',
            'content' => $userMessage,
            'timestamp' => now()->toIso8601String(),
        ];
        $history[] = [
            'role' => 'assistant',
            'content' => $assistantMessage,
            'timestamp' => now()->toIso8601String(),
            'complete' => $complete,
        ];

        $this->saveSessionHistory($sessionId, $history);
    }
}

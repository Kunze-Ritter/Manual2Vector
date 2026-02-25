<?php

namespace App\Services;

use App\Models\ChatMessage;
use App\Models\ChatSession;
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
            $method, $endpoint, $sessionId, $status
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

    // =========================================================================
    // Session Management (DB-based for logged-in users)
    // =========================================================================

    public function generateSessionId(mixed $userId = null): string
    {
        $prefix = $this->sessionConfig['default_session_prefix'] ?? 'krai_chat_';
        $sessionKey = $prefix . ($userId ?? uniqid()) . '_' . time();

        if ($userId) {
            ChatSession::firstOrCreate(
                ['session_key' => $sessionKey],
                [
                    'user_id'     => (string) $userId,
                    'title'       => 'Chat ' . now()->format('d.m.Y H:i'),
                    'last_active' => now(),
                ]
            );
        }

        return $sessionKey;
    }

    public function getSessionHistory(string $sessionId): array
    {
        $session = ChatSession::where('session_key', $sessionId)->first();

        if (!$session) {
            // Fallback to cache for sessions without a DB record
            return Cache::get("ai_agent.session.{$sessionId}", []);
        }

        return $session->messages->map(fn ($m) => [
            'role'      => $m->role,
            'content'   => $m->content,
            'timestamp' => $m->created_at?->toIso8601String() ?? now()->toIso8601String(),
        ])->toArray();
    }

    public function saveSessionHistory(string $sessionId, array $history): void
    {
        // Legacy cache fallback (used by sessions without DB records)
        $ttl = $this->cacheTtl['session_history'] ?? 3600;
        $maxLength = $this->sessionConfig['max_history_length'] ?? 50;
        if (count($history) > $maxLength) {
            $history = array_slice($history, -$maxLength);
        }
        Cache::put("ai_agent.session.{$sessionId}", $history, $ttl);
    }

    public function clearSessionHistory(string $sessionId): void
    {
        Cache::forget("ai_agent.session.{$sessionId}");

        $session = ChatSession::where('session_key', $sessionId)->first();
        if ($session) {
            $session->messages()->delete();
            $session->touch();
        }
    }

    public function appendExchange(string $sessionId, string $userMessage, string $assistantMessage, bool $complete = true): void
    {
        $session = ChatSession::where('session_key', $sessionId)->first();

        if ($session) {
            // Persist to database
            ChatMessage::insert([
                [
                    'session_id' => $session->id,
                    'role'       => 'user',
                    'content'    => $userMessage,
                    'created_at' => now(),
                ],
                [
                    'session_id' => $session->id,
                    'role'       => 'assistant',
                    'content'    => $assistantMessage,
                    'created_at' => now(),
                ],
            ]);
            $session->update(['last_active' => now()]);

            // Enforce max history limit
            $maxLength = $this->sessionConfig['max_history_length'] ?? 50;
            $count = $session->messages()->count();
            if ($count > $maxLength) {
                $session->messages()
                    ->orderBy('created_at')
                    ->limit($count - $maxLength)
                    ->delete();
            }
        } else {
            // Fallback to cache
            $history = $this->getSessionHistory($sessionId);
            $history[] = ['role' => 'user',      'content' => $userMessage,      'timestamp' => now()->toIso8601String()];
            $history[] = ['role' => 'assistant',  'content' => $assistantMessage, 'timestamp' => now()->toIso8601String(), 'complete' => $complete];
            $this->saveSessionHistory($sessionId, $history);
        }
    }

    // =========================================================================
    // Chat API calls
    // =========================================================================

    /**
     * Chat with AI agent (single response).
     */
    public function chat(string $message, string $sessionId): array
    {
        $endpoint = '/chat';

        try {
            $client = $this->createHttpClient($this->timeouts['chat'] ?? 60);
            $response = $client->post($this->baseUrl . $endpoint, [
                'message'    => $message,
                'session_id' => $sessionId,
                'stream'     => false,
            ]);

            $this->logApiCall('POST', $endpoint, $sessionId, $response->status());

            if ($response->successful()) {
                $data = $response->json();
                return [
                    'success' => true,
                    'data' => [
                        'response'   => $data['response'] ?? '',
                        'session_id' => $data['session_id'] ?? $sessionId,
                        'timestamp'  => $data['timestamp'] ?? now()->toIso8601String(),
                    ],
                    'error' => null,
                ];
            }

            $error = $response->json('detail', 'Unknown error');
            $this->logApiCall('POST', $endpoint, $sessionId, $response->status(), $error);
            return ['success' => false, 'data' => ['response' => '', 'session_id' => $sessionId, 'timestamp' => now()->toIso8601String()], 'error' => $error];

        } catch (\Exception $e) {
            $errorInfo = $this->classifyConnectionError($e, $this->baseUrl . $endpoint, $this->timeouts['chat'] ?? 60);
            $this->logApiCall('POST', $endpoint, $sessionId, 500, $errorInfo['message']);
            Log::error('AI Agent chat request failed', $errorInfo + ['session_id' => $sessionId]);
            return ['success' => false, 'data' => ['response' => '', 'session_id' => $sessionId, 'timestamp' => now()->toIso8601String()], 'error' => $errorInfo['message'], 'error_type' => $errorInfo['type'], 'attempted_url' => $errorInfo['url']];
        }
    }

    /**
     * Stream chat response – true token-by-token SSE proxy.
     */
    public function chatStream(string $message, string $sessionId): StreamedResponse
    {
        $endpoint = '/chat/stream';
        $baseUrl  = $this->baseUrl;
        $timeout  = $this->timeouts['stream'] ?? 120;
        $jwt      = $this->serviceJwt;

        return new StreamedResponse(function () use ($message, $sessionId, $endpoint, $baseUrl, $timeout, $jwt) {
            $fullResponse   = '';
            $streamComplete = false;

            try {
                $headers = ['Content-Type' => 'application/json', 'Accept' => 'text/event-stream'];
                if ($jwt) {
                    $headers['Authorization'] = 'Bearer ' . $jwt;
                }

                // Use Guzzle directly for true streaming
                $client = new \GuzzleHttp\Client(['timeout' => $timeout]);
                $guzzleResponse = $client->post($baseUrl . $endpoint, [
                    'json'    => ['message' => $message, 'session_id' => $sessionId, 'stream' => true],
                    'headers' => $headers,
                    'stream'  => true,
                ]);

                $body = $guzzleResponse->getBody();
                $buffer = '';

                while (!$body->eof()) {
                    $buffer .= $body->read(256);

                    // Process complete SSE events (delimited by \n\n)
                    while (($pos = strpos($buffer, "\n\n")) !== false) {
                        $event  = substr($buffer, 0, $pos);
                        $buffer = substr($buffer, $pos + 2);

                        foreach (explode("\n", $event) as $line) {
                            if (!str_starts_with($line, 'data: ')) {
                                continue;
                            }
                            $data = substr($line, 6);
                            if ($data === '[DONE]') {
                                $streamComplete = true;
                                break 2;
                            }
                            try {
                                $json = json_decode($data, true, 512, JSON_THROW_ON_ERROR);
                                if (isset($json['chunk']) && $json['chunk'] !== '') {
                                    $fullResponse .= $json['chunk'];
                                    echo 'data: ' . json_encode(['chunk' => $json['chunk']]) . "\n\n";
                                    if (ob_get_level() > 0) ob_flush();
                                    flush();
                                }
                                if (isset($json['error'])) {
                                    echo 'data: ' . json_encode(['error' => $json['error']]) . "\n\n";
                                    if (ob_get_level() > 0) ob_flush();
                                    flush();
                                }
                            } catch (JsonException) {}
                        }
                    }
                }

                if ($fullResponse) {
                    $this->appendExchange($sessionId, $message, $fullResponse, true);
                }
                $this->logApiCall('POST', $endpoint, $sessionId, 200);

            } catch (\Exception $e) {
                $errorInfo = $this->classifyConnectionError($e, $baseUrl . $endpoint, $timeout);
                Log::error('AI Agent chat stream failed', $errorInfo + ['session_id' => $sessionId]);
                if (!$streamComplete && $fullResponse) {
                    $this->appendExchange($sessionId, $message, $fullResponse, false);
                }
                echo 'data: ' . json_encode(['error' => $errorInfo['message']]) . "\n\n";
                if (ob_get_level() > 0) ob_flush();
                flush();
            }

            echo "data: [DONE]\n\n";
            if (ob_get_level() > 0) ob_flush();
            flush();

        }, 200, [
            'Content-Type'    => 'text/event-stream',
            'Cache-Control'   => 'no-cache',
            'X-Accel-Buffering' => 'no',
        ]);
    }

    // =========================================================================
    // Health check
    // =========================================================================

    public function health(): array
    {
        $endpoint = '/health';

        try {
            $client   = $this->createHttpClient($this->timeouts['health'] ?? 5);
            $response = $client->get($this->baseUrl . $endpoint);

            if ($response->successful()) {
                $data = $response->json();
                return ['success' => true, 'data' => ['status' => $data['status'] ?? 'unknown', 'agent' => $data['agent'] ?? 'KRAI AI Agent', 'version' => $data['version'] ?? '1.0.0'], 'error' => null];
            }

            return ['success' => false, 'data' => ['status' => 'unhealthy', 'agent' => 'KRAI AI Agent', 'version' => '1.0.0'], 'error' => 'HTTP ' . $response->status() . ': ' . $response->body()];

        } catch (\Exception $e) {
            $errorInfo = $this->classifyConnectionError($e, $this->baseUrl . $endpoint, $this->timeouts['health'] ?? 5);
            Log::error('AI Agent health check failed', $errorInfo);
            return ['success' => false, 'data' => ['status' => 'unreachable', 'agent' => 'KRAI AI Agent', 'version' => '1.0.0'], 'error' => $errorInfo['message'], 'error_type' => $errorInfo['type'], 'attempted_url' => $errorInfo['url']];
        }
    }

    // =========================================================================
    // Helpers
    // =========================================================================

    private function classifyConnectionError(\Exception $e, string $url, ?int $timeoutSeconds = null): array
    {
        $message  = $e->getMessage();
        $hostname = parse_url($url, PHP_URL_HOST) ?? 'unknown';

        if (str_contains($message, 'Could not resolve host') || str_contains($message, 'getaddrinfo failed')) {
            return ['type' => 'dns', 'message' => "Service unreachable: DNS resolution failed for {$hostname}", 'url' => $url];
        }
        if (str_contains($message, 'timed out') || str_contains($message, 'timeout')) {
            $t = $timeoutSeconds ?? $this->timeouts['health'] ?? 5;
            return ['type' => 'timeout', 'message' => "Service unreachable: Connection timeout after {$t}s", 'url' => $url];
        }
        if (str_contains($message, 'Connection refused') || str_contains($message, 'Failed to connect')) {
            return ['type' => 'refused', 'message' => "Service unreachable: Connection refused (service may be down)", 'url' => $url];
        }
        return ['type' => 'connection', 'message' => "Connection error: {$message}", 'url' => $url];
    }
}

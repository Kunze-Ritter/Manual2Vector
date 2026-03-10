<?php

namespace App\Services;

use App\Enums\ChatMessageRole;
use App\Models\ChatMessage;
use App\Models\ChatSession;
use App\Models\Document;
use App\Models\ErrorCode;
use App\Models\Product;
use Illuminate\Http\Client\PendingRequest;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use JsonException;
use Symfony\Component\HttpFoundation\StreamedResponse;

class AiAgentService
{
    public function __construct(
        private ?string $baseUrl = null,
        private ?string $serviceJwt = null,
        private ?array $timeouts = null,
        private ?array $cacheTtl = null,
        private ?array $sessionConfig = null,
    ) {
        $this->baseUrl = rtrim($baseUrl ?? config('krai.ai_agent.base_url'), '/');
        $this->serviceJwt = $serviceJwt ?? config('krai.service_jwt');
        $this->timeouts = $timeouts ?? config('krai.ai_agent.timeout', []);
        $this->cacheTtl = $cacheTtl ?? config('krai.ai_agent.cache_ttl', []);
        $this->sessionConfig = $sessionConfig ?? config('krai.ai_agent.session', []);
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
                'Authorization' => 'Bearer '.$this->serviceJwt,
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
            $message .= ' - Error: '.$error;
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
        $sessionKey = $prefix.($userId ?? uniqid()).'_'.time();

        if ($userId) {
            ChatSession::firstOrCreate(
                ['session_key' => $sessionKey],
                [
                    'user_id' => (string) $userId,
                    'title' => 'Chat '.now()->format('d.m.Y H:i'),
                    'last_active' => now(),
                ]
            );
        }

        return $sessionKey;
    }

    public function getUserSessions(string $userId): array
    {
        try {
            return ChatSession::where('user_id', $userId)
                ->orderByDesc('last_active')
                ->limit(30)
                ->get()
                ->map(fn ($s) => [
                    'id' => (string) $s->id,
                    'session_key' => $s->session_key,
                    'title' => $s->title ?? '',
                    'last_active' => $s->last_active?->toIso8601String() ?? $s->updated_at?->toIso8601String() ?? now()->toIso8601String(),
                ])
                ->toArray();
        } catch (\Throwable $e) {
            Log::error('getUserSessions failed', ['user_id' => $userId, 'error' => $e->getMessage()]);

            return [];
        }
    }

    public function createNewSession(string $userId, string $title = ''): string
    {
        $prefix = $this->sessionConfig['default_session_prefix'] ?? 'krai_chat_';
        $sessionKey = $prefix.$userId.'_'.time();

        ChatSession::create([
            'user_id' => $userId,
            'session_key' => $sessionKey,
            'title' => $title ?: 'Chat '.now()->format('d.m.Y H:i'),
            'last_active' => now(),
        ]);

        return $sessionKey;
    }

    public function renameSession(string $sessionKey, string $title): void
    {
        ChatSession::where('session_key', $sessionKey)->update(['title' => $title]);
    }

    public function deleteSession(string $sessionKey): void
    {
        $session = ChatSession::where('session_key', $sessionKey)->first();
        if ($session) {
            $session->messages()->delete();
            $session->delete();
        }
    }

    public function addUserMessage(string $sessionId, string $content): void
    {
        $session = ChatSession::where('session_key', $sessionId)->first();
        if (! $session) {
            return;
        }

        ChatMessage::create([
            'session_id' => $session->id,
            'role' => ChatMessageRole::User->value,
            'content' => $content,
            'created_at' => now(),
        ]);
    }

    public function addAssistantMessage(string $sessionId, string $content): void
    {
        $session = ChatSession::where('session_key', $sessionId)->first();
        if (! $session) {
            return;
        }

        ChatMessage::create([
            'session_id' => $session->id,
            'role' => ChatMessageRole::Assistant->value,
            'content' => $content,
            'created_at' => now(),
        ]);

        $session->update(['last_active' => now()]);

        $maxLength = $this->sessionConfig['max_history_length'] ?? 50;
        $count = $session->messages()->count();
        if ($count > $maxLength) {
            $session->messages()
                ->orderBy('created_at')
                ->limit($count - $maxLength)
                ->delete();
        }
    }

    public function getSessionHistory(string $sessionId): array
    {
        $session = ChatSession::where('session_key', $sessionId)->first();

        if (! $session) {
            return Cache::get("ai_agent.session.{$sessionId}", []);
        }

        return $session->messages->map(fn ($m) => [
            'role' => $m->role?->value ?? (string) $m->getRawOriginal('role'),
            'content' => $m->content,
            'timestamp' => $m->created_at?->toIso8601String() ?? now()->toIso8601String(),
        ])->toArray();
    }

    public function saveSessionHistory(string $sessionId, array $history): void
    {
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
            ChatMessage::insert([
                [
                    'session_id' => $session->id,
                    'role' => ChatMessageRole::User->value,
                    'content' => $userMessage,
                    'created_at' => now(),
                ],
                [
                    'session_id' => $session->id,
                    'role' => ChatMessageRole::Assistant->value,
                    'content' => $assistantMessage,
                    'created_at' => now(),
                ],
            ]);
            $session->update(['last_active' => now()]);

            $maxLength = $this->sessionConfig['max_history_length'] ?? 50;
            $count = $session->messages()->count();
            if ($count > $maxLength) {
                $session->messages()
                    ->orderBy('created_at')
                    ->limit($count - $maxLength)
                    ->delete();
            }
        } else {
            $history = $this->getSessionHistory($sessionId);
            $history[] = ['role' => ChatMessageRole::User->value, 'content' => $userMessage, 'timestamp' => now()->toIso8601String()];
            $history[] = ['role' => ChatMessageRole::Assistant->value, 'content' => $assistantMessage, 'timestamp' => now()->toIso8601String(), 'complete' => $complete];
            $this->saveSessionHistory($sessionId, $history);
        }
    }

    // =========================================================================
    // Chat API calls
    // =========================================================================

    public function chat(string $message, string $sessionId): array
    {
        $message = trim($message);

        if (str_starts_with($message, '/')) {
            return $this->handleSlashCommand($message, $sessionId);
        }

        $endpoint = '/chat';

        try {
            $client = $this->createHttpClient($this->timeouts['chat'] ?? 60);
            $response = $client->post($this->baseUrl.$endpoint, [
                'message' => $message,
                'session_id' => $sessionId,
                'stream' => false,
            ]);

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

            return ['success' => false, 'data' => ['response' => '', 'session_id' => $sessionId, 'timestamp' => now()->toIso8601String()], 'error' => $error];

        } catch (\Exception $e) {
            $errorInfo = $this->classifyConnectionError($e, $this->baseUrl.$endpoint, $this->timeouts['chat'] ?? 60);
            $this->logApiCall('POST', $endpoint, $sessionId, 500, $errorInfo['message']);
            Log::error('AI Agent chat request failed', $errorInfo + ['session_id' => $sessionId]);

            return ['success' => false, 'data' => ['response' => '', 'session_id' => $sessionId, 'timestamp' => now()->toIso8601String()], 'error' => $errorInfo['message'], 'error_type' => $errorInfo['type'], 'attempted_url' => $errorInfo['url']];
        }
    }

    private function handleSlashCommand(string $input, string $sessionId): array
    {
        $payload = trim($input);
        $parts = preg_split('/\s+/', $payload, 2) ?: [];
        $command = Str::lower(ltrim($parts[0] ?? '', '/'));
        $args = trim($parts[1] ?? '');

        return match ($command) {
            'help' => $this->commandResult(
                $sessionId,
                "Verfuegbare Commands:\n".
                "- `/help` Uebersicht\n".
                "- `/errors <suchbegriff> [limit]` Fehlercodes suchen\n".
                "- `/products <suchbegriff> [limit]` Produkte suchen\n".
                "- `/docs <suchbegriff> [limit]` Dokumente suchen\n".
                "- `/stats` KPI Snapshot\n".
                "- `/sql <SELECT ...>` SQL-Read-Only (nur Admin)"
            ),
            'errors' => $this->findErrorsCommand($sessionId, $args),
            'products' => $this->findProductsCommand($sessionId, $args),
            'docs' => $this->findDocumentsCommand($sessionId, $args),
            'stats' => $this->statsCommand($sessionId),
            'sql' => $this->sqlCommand($sessionId, $args),
            default => $this->commandResult(
                $sessionId,
                "Unbekannter Command: `/{$command}`\nNutze `/help` fuer verfuegbare Commands."
            ),
        };
    }

    private function findErrorsCommand(string $sessionId, string $args): array
    {
        [$query, $limit] = $this->parseSearchArgs($args, 8);
        if ($query === '') {
            return $this->commandResult($sessionId, 'Usage: `/errors <suchbegriff> [limit]`');
        }

        $rows = ErrorCode::query()
            ->with(['product', 'manufacturer'])
            ->where(function ($q) use ($query) {
                $q->where('error_code', 'ilike', "%{$query}%")
                    ->orWhere('error_description', 'ilike', "%{$query}%")
                    ->orWhere('solution_text', 'ilike', "%{$query}%");
            })
            ->orderByDesc('updated_at')
            ->limit($limit)
            ->get();

        if ($rows->isEmpty()) {
            return $this->commandResult($sessionId, "Keine Treffer fuer `{$query}`.");
        }

        $lines = ["Treffer fuer `{$query}` (".$rows->count()."):"];
        foreach ($rows as $r) {
            $manufacturer = $r->manufacturer?->name ?? 'N/A';
            $model = $r->product?->model_number ?? 'N/A';
            $desc = Str::limit((string) ($r->error_description ?? ''), 120);
            $solution = Str::limit((string) ($r->solution_text ?? ''), 120);
            $lines[] = "- **{$r->error_code}** | {$manufacturer} {$model}\n  {$desc}\n  Loesung: {$solution}";
        }

        return $this->commandResult($sessionId, implode("\n", $lines));
    }

    private function findProductsCommand(string $sessionId, string $args): array
    {
        [$query, $limit] = $this->parseSearchArgs($args, 8);
        if ($query === '') {
            return $this->commandResult($sessionId, 'Usage: `/products <suchbegriff> [limit]`');
        }

        $rows = Product::query()
            ->with(['manufacturer', 'series'])
            ->where(function ($q) use ($query) {
                $q->where('model_number', 'ilike', "%{$query}%")
                    ->orWhere('product_code', 'ilike', "%{$query}%")
                    ->orWhere('article_code', 'ilike', "%{$query}%")
                    ->orWhere('product_type', 'ilike', "%{$query}%");
            })
            ->orderByDesc('updated_at')
            ->limit($limit)
            ->get();

        if ($rows->isEmpty()) {
            return $this->commandResult($sessionId, "Keine Produkte fuer `{$query}` gefunden.");
        }

        $lines = ["Produkte fuer `{$query}` (".$rows->count()."):"];
        foreach ($rows as $r) {
            $manufacturer = $r->manufacturer?->name ?? 'N/A';
            $series = $r->series?->series_name ?? 'N/A';
            $code = $r->product_code ?: ($r->article_code ?: 'N/A');
            $lines[] = "- **{$r->model_number}** | {$manufacturer} | Serie: {$series} | Code: {$code} | Typ: ".($r->product_type ?? 'N/A');
        }

        return $this->commandResult($sessionId, implode("\n", $lines));
    }

    private function findDocumentsCommand(string $sessionId, string $args): array
    {
        [$query, $limit] = $this->parseSearchArgs($args, 8);
        if ($query === '') {
            return $this->commandResult($sessionId, 'Usage: `/docs <suchbegriff> [limit]`');
        }

        $rows = Document::query()
            ->where(function ($q) use ($query) {
                $q->where('filename', 'ilike', "%{$query}%")
                    ->orWhere('document_type', 'ilike', "%{$query}%")
                    ->orWhere('manufacturer', 'ilike', "%{$query}%")
                    ->orWhere('series', 'ilike', "%{$query}%");
            })
            ->orderByDesc('updated_at')
            ->limit($limit)
            ->get();

        if ($rows->isEmpty()) {
            return $this->commandResult($sessionId, "Keine Dokumente fuer `{$query}` gefunden.");
        }

        $lines = ["Dokumente fuer `{$query}` (".$rows->count()."):"];
        foreach ($rows as $r) {
            $status = $r->processing_status ?? 'unknown';
            $lines[] = "- **{$r->filename}** | Typ: ".($r->document_type ?? 'N/A')." | Sprache: ".($r->language ?? 'N/A')." | Status: {$status}";
        }

        return $this->commandResult($sessionId, implode("\n", $lines));
    }

    private function statsCommand(string $sessionId): array
    {
        $products = Product::count();
        $errors = ErrorCode::count();
        $documents = Document::count();
        $sessions = ChatSession::count();
        $messages = ChatMessage::count();

        return $this->commandResult(
            $sessionId,
            "KRAI Snapshot:\n".
            "- Produkte: **{$products}**\n".
            "- Fehlercodes: **{$errors}**\n".
            "- Dokumente: **{$documents}**\n".
            "- Chat Sessions: **{$sessions}**\n".
            "- Chat Messages: **{$messages}**"
        );
    }

    private function sqlCommand(string $sessionId, string $args): array
    {
        $user = Auth::user();
        if (! $user || ! method_exists($user, 'isAdmin') || ! $user->isAdmin()) {
            return $this->commandResult($sessionId, 'SQL Command ist nur fuer Admins erlaubt.');
        }

        $sql = trim($args);
        if ($sql === '') {
            return $this->commandResult($sessionId, 'Usage: `/sql SELECT ...`');
        }

        if (! preg_match('/^\s*(select|with)\b/i', $sql)) {
            return $this->commandResult($sessionId, 'Nur `SELECT` oder `WITH` Statements sind erlaubt.');
        }

        if (preg_match('/;|--|\/\*|\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|copy|vacuum|analyze|call|do)\b/i', $sql)) {
            return $this->commandResult($sessionId, 'Unsicheres SQL blockiert. Nur einfache Read-Only Queries ohne Kommentare/Mehrfach-Statements.');
        }

        if (! preg_match('/\blimit\s+\d+\b/i', $sql)) {
            $sql .= ' LIMIT 50';
        }

        try {
            $rows = collect(DB::select($sql))->map(fn ($row) => (array) $row)->values();
            if ($rows->isEmpty()) {
                return $this->commandResult($sessionId, "SQL erfolgreich, 0 Zeilen.\n```sql\n{$sql}\n```");
            }

            $preview = $rows->take(20)->toJson(JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

            return $this->commandResult(
                $sessionId,
                "SQL erfolgreich, {$rows->count()} Zeilen (Preview max 20):\n```sql\n{$sql}\n```\n```json\n{$preview}\n```"
            );
        } catch (\Throwable $e) {
            return $this->commandResult($sessionId, 'SQL Fehler: '.$e->getMessage());
        }
    }

    private function parseSearchArgs(string $args, int $defaultLimit = 8): array
    {
        $parts = preg_split('/\s+/', trim($args)) ?: [];
        $limit = $defaultLimit;

        if (! empty($parts) && ctype_digit(end($parts))) {
            $limit = max(1, min(50, (int) array_pop($parts)));
        }

        return [trim(implode(' ', $parts)), $limit];
    }

    private function commandResult(string $sessionId, string $response): array
    {
        return [
            'success' => true,
            'data' => [
                'response' => $response,
                'session_id' => $sessionId,
                'timestamp' => now()->toIso8601String(),
            ],
            'error' => null,
        ];
    }

    public function chatStream(string $message, string $sessionId): StreamedResponse
    {
        $endpoint = '/chat/stream';
        $baseUrl = $this->baseUrl;
        $timeout = $this->timeouts['stream'] ?? 120;
        $jwt = $this->serviceJwt;

        return new StreamedResponse(function () use ($message, $sessionId, $endpoint, $baseUrl, $timeout, $jwt) {
            try {
                $headers = ['Content-Type' => 'application/json', 'Accept' => 'text/event-stream'];
                if ($jwt) {
                    $headers['Authorization'] = 'Bearer '.$jwt;
                }

                $client = new \GuzzleHttp\Client(['timeout' => $timeout]);
                $guzzleResponse = $client->post($baseUrl.$endpoint, [
                    'json' => ['message' => $message, 'session_id' => $sessionId, 'stream' => true],
                    'headers' => $headers,
                    'stream' => true,
                ]);

                $body = $guzzleResponse->getBody();
                $buffer = '';

                while (! $body->eof()) {
                    $buffer .= $body->read(256);

                    while (($pos = strpos($buffer, "\n\n")) !== false) {
                        $event = substr($buffer, 0, $pos);
                        $buffer = substr($buffer, $pos + 2);

                        foreach (explode("\n", $event) as $line) {
                            if (! str_starts_with($line, 'data: ')) {
                                continue;
                            }
                            $data = substr($line, 6);
                            if ($data === '[DONE]') {
                                break 2;
                            }
                            try {
                                $json = json_decode($data, true, 512, JSON_THROW_ON_ERROR);
                                if (isset($json['chunk']) && $json['chunk'] !== '') {
                                    echo 'data: '.json_encode(['chunk' => $json['chunk']])."\n\n";
                                    if (ob_get_level() > 0) {
                                        ob_flush();
                                    }
                                    flush();
                                }
                                if (isset($json['error'])) {
                                    echo 'data: '.json_encode(['error' => $json['error']])."\n\n";
                                    if (ob_get_level() > 0) {
                                        ob_flush();
                                    }
                                    flush();
                                }
                            } catch (JsonException) {
                            }
                        }
                    }
                }

                $this->logApiCall('POST', $endpoint, $sessionId, 200);

            } catch (\Exception $e) {
                $errorInfo = $this->classifyConnectionError($e, $baseUrl.$endpoint, $timeout);
                Log::error('AI Agent chat stream failed', $errorInfo + ['session_id' => $sessionId]);
                echo 'data: '.json_encode(['error' => $errorInfo['message']])."\n\n";
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

        }, 200, [
            'Content-Type' => 'text/event-stream',
            'Cache-Control' => 'no-cache',
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
            $client = $this->createHttpClient($this->timeouts['health'] ?? 5);
            $response = $client->get($this->baseUrl.$endpoint);

            if ($response->successful()) {
                $data = $response->json();

                return ['success' => true, 'data' => ['status' => $data['status'] ?? 'unknown', 'agent' => $data['agent'] ?? 'KRAI AI Agent', 'version' => $data['version'] ?? '1.0.0'], 'error' => null];
            }

            return ['success' => false, 'data' => ['status' => 'unhealthy', 'agent' => 'KRAI AI Agent', 'version' => '1.0.0'], 'error' => 'HTTP '.$response->status().': '.$response->body()];

        } catch (\Exception $e) {
            $errorInfo = $this->classifyConnectionError($e, $this->baseUrl.$endpoint, $this->timeouts['health'] ?? 5);
            Log::error('AI Agent health check failed', $errorInfo);

            return ['success' => false, 'data' => ['status' => 'unreachable', 'agent' => 'KRAI AI Agent', 'version' => '1.0.0'], 'error' => $errorInfo['message'], 'error_type' => $errorInfo['type'], 'attempted_url' => $errorInfo['url']];
        }
    }

    // =========================================================================
    // Helpers
    // =========================================================================

    private function classifyConnectionError(\Exception $e, string $url, ?int $timeoutSeconds = null): array
    {
        $message = $e->getMessage();
        $hostname = parse_url($url, PHP_URL_HOST) ?? 'unknown';

        if (str_contains($message, 'Could not resolve host') || str_contains($message, 'getaddrinfo failed')) {
            return ['type' => 'dns', 'message' => "Service unreachable: DNS resolution failed for {$hostname}", 'url' => $url];
        }
        if (str_contains($message, 'timed out') || str_contains($message, 'timeout')) {
            $t = $timeoutSeconds ?? $this->timeouts['health'] ?? 5;

            return ['type' => 'timeout', 'message' => "Service unreachable: Connection timeout after {$t}s", 'url' => $url];
        }
        if (str_contains($message, 'Connection refused') || str_contains($message, 'Failed to connect')) {
            return ['type' => 'refused', 'message' => 'Service unreachable: Connection refused (service may be down)', 'url' => $url];
        }

        return ['type' => 'connection', 'message' => "Connection error: {$message}", 'url' => $url];
    }
}

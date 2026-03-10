<?php

namespace App\Filament\Pages;

use App\Services\AiAgentService;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Filament\Support\Enums\Width;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class AiChatPage extends Page
{
    protected string $view = 'filament.pages.ai-chat-page';

    protected static \BackedEnum|string|null $navigationIcon = 'heroicon-o-chat-bubble-left-right';

    protected static ?string $navigationLabel = 'AI Chat';

    protected static \UnitEnum|string|null $navigationGroup = 'Services';

    protected static ?int $navigationSort = 1;

    protected ?string $heading = '';

    protected ?string $subheading = '';

    public function getMaxContentWidth(): Width|string|null
    {
        return Width::Full;
    }

    public array $messages = [];

    public array $chatSessions = [];

    public string $sessionId = '';

    public string $sessionTitle = '';

    public string $currentMessage = '';

    public bool $isStreaming = false;

    public bool $agentAvailable = true;

    public ?string $agentErrorMessage = null;

    public ?string $agentErrorType = null;

    public function mount(): void
    {
        try {
            $health = $this->getAgentHealth();

            if (! ($health['success'] ?? false)) {
                $this->agentAvailable = false;
                $this->agentErrorMessage = $health['error'] ?? 'AI Agent ist nicht verfügbar';
                $this->agentErrorType = $health['error_type'] ?? 'unknown';

                Notification::make()
                    ->title('AI Agent nicht erreichbar')
                    ->body($this->agentErrorMessage)
                    ->danger()
                    ->persistent()
                    ->send();

                return;
            }

            $this->loadSessions();

            if (empty($this->chatSessions)) {
                $this->sessionId = $this->getAiAgent()->createNewSession((string) Auth::id());
                $this->loadSessions();
            } else {
                $this->sessionId = $this->chatSessions[0]['session_key'];
            }

            $this->sessionTitle = collect($this->chatSessions)->firstWhere('session_key', $this->sessionId)['title'] ?? '';
            $this->messages = $this->getAiAgent()->getSessionHistory($this->sessionId);

        } catch (\Throwable $e) {
            $this->agentAvailable = false;
            $this->agentErrorMessage = $e->getMessage();
            $this->messages = [];
            Log::error('AiChatPage mount failed: '.$e->getMessage());
        }
    }

    public function loadSessions(): void
    {
        try {
            $this->chatSessions = $this->getAiAgent()->getUserSessions((string) Auth::id());
        } catch (\Throwable $e) {
            Log::error('AiChatPage loadSessions failed: '.$e->getMessage());
            $this->chatSessions = [];
        }
    }

    public function newChat(): void
    {
        $this->sessionId = $this->getAiAgent()->createNewSession((string) Auth::id());
        Cache::forget('ai_agent.workspace_snapshot');
        $this->loadSessions();
        $this->sessionTitle = collect($this->chatSessions)->firstWhere('session_key', $this->sessionId)['title'] ?? '';
        $this->messages = [];
        $this->currentMessage = '';
        $this->isStreaming = false;
    }

    public function switchSession(string $sessionKey): void
    {
        $this->sessionId = $sessionKey;
        $this->sessionTitle = collect($this->chatSessions)->firstWhere('session_key', $sessionKey)['title'] ?? '';
        $this->messages = $this->getAiAgent()->getSessionHistory($sessionKey);
        $this->isStreaming = false;
    }

    public function deleteSession(string $sessionKey): void
    {
        $this->getAiAgent()->deleteSession($sessionKey);
        Cache::forget('ai_agent.workspace_snapshot');
        $this->loadSessions();

        if ($this->sessionId === $sessionKey) {
            if (! empty($this->chatSessions)) {
                $this->switchSession($this->chatSessions[0]['session_key']);
            } else {
                $this->newChat();
            }
        }
    }

    public function sendMessage(): void
    {
        $message = trim($this->currentMessage);

        if (empty($message)) {
            return;
        }

        if ($this->sessionId === '') {
            $this->newChat();
        }

        $health = $this->getAgentHealth();
        if (! ($health['success'] ?? false)) {
            Notification::make()
                ->title('AI Agent ist offline')
                ->body($health['error'] ?? 'Nachricht kann nicht gesendet werden.')
                ->danger()
                ->send();
            return;
        }

        $this->addUserMessage($message);
        $this->currentMessage = '';

        try {
            $aiAgent = $this->getAiAgent();
            $result = $aiAgent->chat($message, $this->sessionId);

            if ($result['success']) {
                $response = $result['data']['response'] ?? 'Keine Antwort erhalten.';
                $this->saveAssistantMessage($response);
            } else {
                $errorMsg = $result['error'] ?? 'Unbekannter Fehler';
                $this->saveAssistantMessage("Entschuldigung, es ist ein Fehler aufgetreten: {$errorMsg}");
                
                Notification::make()
                    ->title('Fehler')
                    ->body($errorMsg)
                    ->danger()
                    ->send();
            }
        } catch (\Throwable $e) {
            Log::error('Chat sendMessage failed: '.$e->getMessage());
            $this->saveAssistantMessage("Entschuldigung, es ist ein Fehler aufgetreten: {$e->getMessage()}");
        }
    }

    public function addUserMessage(string $message): void
    {
        $this->getAiAgent()->addUserMessage($this->sessionId, $message);
        Cache::forget('ai_agent.workspace_snapshot');

        $this->messages[] = [
            'role' => 'user',
            'content' => $message,
            'timestamp' => now()->toIso8601String(),
        ];

        $this->isStreaming = true;
        $this->loadSessions();
    }

    public function saveAssistantMessage(string $content): void
    {
        $this->getAiAgent()->addAssistantMessage($this->sessionId, $content);
        Cache::forget('ai_agent.workspace_snapshot');

        $this->messages[] = [
            'role' => 'assistant',
            'content' => $content,
            'timestamp' => now()->toIso8601String(),
        ];

        $this->isStreaming = false;
        $this->loadSessions();

        if (count($this->messages) === 2) {
            $firstUserMessage = collect($this->messages)->firstWhere('role', 'user')['content'] ?? '';
            if ($firstUserMessage) {
                $title = mb_substr($firstUserMessage, 0, 50);
                $this->getAiAgent()->renameSession($this->sessionId, $title);
                $this->sessionTitle = $title;
                $this->loadSessions();
            }
        }
    }

    public function clearHistory(): void
    {
        $this->getAiAgent()->clearSessionHistory($this->sessionId);
        Cache::forget('ai_agent.workspace_snapshot');
        $this->messages = [];

        Notification::make()
            ->title('Chat-Verlauf gelöscht')
            ->success()
            ->send();
    }

    public function refreshMessages(): void
    {
        if (empty($this->sessionId)) {
            return;
        }

        try {
            $this->messages = $this->getAiAgent()->getSessionHistory($this->sessionId);
            $this->loadSessions();
        } catch (\Throwable $e) {
            Log::warning('AiChatPage refreshMessages failed: '.$e->getMessage());
        }
    }

    public function getAgentHealth(): array
    {
        return Cache::remember('ai_agent.health', 30, function () {
            try {
                $health = $this->getAiAgent()->health();

                if (! ($health['success'] ?? false)) {
                    Log::warning('AI Agent health check failed', [
                        'error' => $health['error'] ?? 'Unknown error',
                    ]);
                }

                return $health;
            } catch (\Throwable $e) {
                Log::error('AI Agent health check exception: '.$e->getMessage());

                return [
                    'success' => false,
                    'error' => $e->getMessage(),
                    'error_type' => 'exception',
                ];
            }
        });
    }

    public function retryConnection(): void
    {
        Cache::forget('ai_agent.health');
        $this->mount();

        if ($this->agentAvailable) {
            Notification::make()
                ->title('Verbindung wiederhergestellt')
                ->body('AI Agent ist jetzt online.')
                ->success()
                ->send();
        }
    }

    protected function getViewData(): array
    {
        $health = $this->getAgentHealth();
        $healthData = $health['data'] ?? [];

        try {
            $commandCatalog = $this->getAiAgent()->getCommandCatalog();
        } catch (\Throwable $e) {
            Log::warning('AiChatPage command catalog unavailable: '.$e->getMessage());
            $commandCatalog = [];
        }

        try {
            $workspaceSnapshot = Cache::remember('ai_agent.workspace_snapshot', 30, fn () => $this->getAiAgent()->getWorkspaceSnapshot());
        } catch (\Throwable $e) {
            Log::warning('AiChatPage workspace snapshot unavailable: '.$e->getMessage());
            $workspaceSnapshot = [
                'products' => 0,
                'errors' => 0,
                'documents' => 0,
                'sessions' => count($this->chatSessions),
                'messages' => count($this->messages),
            ];
        }

        return [
            'chatSessions' => $this->chatSessions,
            'sessions' => $this->chatSessions,
            'sessionId' => $this->sessionId,
            'sessionTitle' => $this->sessionTitle,
            'messages' => $this->messages,
            'isStreaming' => $this->isStreaming,
            'commandCatalog' => $commandCatalog,
            'workspaceSnapshot' => $workspaceSnapshot,
            'agentHealth' => $healthData,
            'healthOk' => $health['success'] ?? false,
            'agentStatus' => $healthData['status'] ?? 'unknown',
            'agentVersion' => $healthData['version'] ?? 'n/a',
            'agentName' => $healthData['agent'] ?? 'KRAI AI Agent',
            'agentErrorMessage' => $this->agentErrorMessage,
            'agentErrorType' => $this->agentErrorType,
        ];
    }

    private function getAiAgent(): AiAgentService
    {
        return app(AiAgentService::class);
    }
}

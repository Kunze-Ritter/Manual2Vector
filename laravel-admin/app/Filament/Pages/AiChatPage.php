<?php

namespace App\Filament\Pages;

use App\Services\AiAgentService;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

class AiChatPage extends Page
{
    protected static \BackedEnum|string|null $navigationIcon = 'heroicon-o-chat-bubble-left-right';

    protected static ?string $navigationLabel = 'AI Chat';

    protected static \UnitEnum|string|null $navigationGroup = 'Services';

    protected static ?int $navigationSort = 1;

    public array $messages = [];

    public string $sessionId = '';

    public string $currentMessage = '';

    public bool $agentAvailable = true;

    public ?string $agentErrorMessage = null;

    public ?string $agentErrorType = null;

    public function mount(): void
    {
        try {
            $health = $this->getAgentHealth();

            if (!($health['success'] ?? false)) {
                $this->agentAvailable = false;
                $this->agentErrorMessage = $health['error'] ?? 'AI Agent ist nicht verfügbar';
                $this->agentErrorType = $health['error_type'] ?? 'unknown';
                $this->messages = [];
                
                // Show detailed error notification
                $errorBody = $this->agentErrorMessage;
                if (config('app.debug') && isset($health['attempted_url'])) {
                    $errorBody .= "\n\nVersuchte URL: " . $health['attempted_url'];
                }
                
                Notification::make()
                    ->title('AI Agent nicht erreichbar')
                    ->body($errorBody)
                    ->danger()
                    ->persistent()
                    ->send();
                return;
            }

            $aiAgent = $this->getAiAgent();
            $this->sessionId = $aiAgent->generateSessionId(Auth::id());
            $this->messages = $aiAgent->getSessionHistory($this->sessionId);
        } catch (\Throwable $e) {
            $this->agentAvailable = false;
            $this->agentErrorMessage = $e->getMessage();
            $this->messages = [];
            Log::error('AiChatPage mount failed: ' . $e->getMessage());
        }
    }

    public function sendMessage(): void
    {
        $this->validate([
            'currentMessage' => ['required', 'string', 'max:1000'],
        ]);

        $health = $this->getAgentHealth();
        if (!($health['success'] ?? false)) {
            $errorBody = $health['error'] ?? 'Nachricht kann aktuell nicht gesendet werden.';
            if (config('app.debug') && isset($health['attempted_url'])) {
                $errorBody .= "\n\nVerbindungs-URL: " . $health['attempted_url'];
            }
            
            Notification::make()
                ->title('AI Agent ist offline')
                ->body($errorBody)
                ->danger()
                ->send();
            return;
        }

        $message = $this->currentMessage;

        $this->dispatchBrowserEvent('chat:streaming-start', [
            'sessionId' => $this->sessionId,
            'message' => $message,
        ]);

        $this->currentMessage = '';
        $this->dispatchBrowserEvent('chat:message-sent');
    }

    public function fallbackChat(string $message): void
    {
        $aiAgent = $this->getAiAgent();
        $result = $aiAgent->chat($message, $this->sessionId);

        if ($result['success']) {
            $aiAgent->appendExchange(
                $this->sessionId,
                $message,
                $result['data']['response'] ?? '',
                true
            );
            $this->refreshMessages();
            return;
        }

        Notification::make()
            ->title('Antwort vom AI Agent fehlgeschlagen')
            ->body($result['error'] ?? 'Unbekannter Fehler')
            ->danger()
            ->send();
    }

    public function clearHistory(): void
    {
        $aiAgent = $this->getAiAgent();
        $aiAgent->clearSessionHistory($this->sessionId);
        $this->messages = [];

        Notification::make()
            ->title('Chat-Verlauf gelöscht')
            ->success()
            ->send();
    }

    public function refreshMessages(): void
    {
        $aiAgent = $this->getAiAgent();
        $this->messages = $aiAgent->getSessionHistory($this->sessionId);
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

    public function getAgentHealth(): array
    {
        return Cache::remember('ai_agent.health', 30, function () {
            try {
                $aiAgent = $this->getAiAgent();
                $health = $aiAgent->health();
                
                if (!($health['success'] ?? false)) {
                    Log::warning('AI Agent health check failed', [
                        'error' => $health['error'] ?? 'Unknown error',
                        'error_type' => $health['error_type'] ?? 'unknown',
                        'url' => $health['attempted_url'] ?? 'unknown',
                    ]);
                }
                
                return $health;
            } catch (\Throwable $e) {
                Log::error('AI Agent health check exception', [
                    'message' => $e->getMessage(),
                    'trace' => $e->getTraceAsString(),
                ]);
                return [
                    'success' => false,
                    'error' => $e->getMessage(),
                    'error_type' => 'exception',
                ];
            }
        });
    }

    /**
     * Get AiAgentService instance on demand.
     * Avoids Livewire lifecycle issues with protected typed properties.
     */
    private function getAiAgent(): AiAgentService
    {
        return app(AiAgentService::class);
    }
}

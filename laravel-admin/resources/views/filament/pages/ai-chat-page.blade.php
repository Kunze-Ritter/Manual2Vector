<x-filament-panels::page>
    @php
        $health = $this->getAgentHealth();
        $healthOk = $health['success'] ?? false;
    @endphp

    @if($healthOk)
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {{-- Chat Interface (Left Column - 2/3 width) --}}
            <div class="lg:col-span-2">
                <x-filament::card>
                    {{-- Header with Status --}}
                    <div class="flex items-center justify-between mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
                        <div class="flex items-center space-x-3">
                            <x-filament::icon icon="heroicon-o-sparkles" class="h-6 w-6 text-primary-500" />
                            <div>
                                <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">KRAI AI Assistant</h3>
                                <x-filament::badge :color="$healthOk ? 'success' : 'danger'" size="sm">
                                    {{ $healthOk ? 'Online' : 'Offline' }}
                                </x-filament::badge>
                            </div>
                        </div>
                    </div>

                    {{-- Messages Container --}}
                    <div 
                        x-data="aiChatPage()"
                        x-init="init()"
                        class="space-y-4"
                    >
                        <div 
                            class="overflow-y-auto space-y-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg h-[calc(100vh-20rem)] md:h-[600px]"
                            x-ref="messagesContainer"
                        >
                            @foreach($messages as $message)
                                @if(($message['role'] ?? '') === 'user')
                                    {{-- User Message --}}
                                    <div class="flex justify-end">
                                        <div class="bg-primary-100 dark:bg-primary-900 text-primary-900 dark:text-primary-100 rounded-lg p-3 max-w-[80%] shadow-sm">
                                            <p class="text-sm whitespace-pre-line">{{ $message['content'] ?? '' }}</p>
                                            <p class="text-[11px] text-gray-500 dark:text-gray-400 mt-1">
                                                {{ \Carbon\Carbon::parse($message['timestamp'] ?? now())->format('H:i') }}
                                            </p>
                                        </div>
                                    </div>
                                @else
                                    {{-- Assistant Message --}}
                                    <div class="flex justify-start">
                                        <div class="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg p-3 max-w-[80%] shadow-sm">
                                            <div class="text-sm prose dark:prose-invert prose-sm max-w-none">
                                                {!! \Illuminate\Support\Str::markdown($message['content'] ?? '') !!}
                                            </div>
                                            <p class="text-[11px] text-gray-500 dark:text-gray-400 mt-1">
                                                {{ \Carbon\Carbon::parse($message['timestamp'] ?? now())->format('H:i') }}
                                            </p>
                                        </div>
                                    </div>
                                @endif
                            @endforeach

                            {{-- Streaming Indicator --}}
                            <div
                                x-show="isStreaming"
                                x-ref="streamingMessage"
                                class="flex justify-start"
                            >
                                <div class="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg p-3 max-w-[80%] shadow-sm">
                                    <div class="flex space-x-1">
                                        <span class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></span>
                                        <span class="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.15s]"></span>
                                        <span class="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.3s]"></span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {{-- Message Input Form --}}
                        <form wire:submit.prevent="sendMessage" class="space-y-3 mt-4">
                            <textarea
                                wire:model.defer="currentMessage"
                                rows="3"
                                placeholder="Frage stellen... (Enter zum Senden, Shift+Enter für neue Zeile)"
                                class="w-full block rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 dark:bg-gray-900 dark:border-gray-700 dark:text-gray-100"
                                x-on:keydown.enter.prevent="if(!$event.shiftKey) $wire.sendMessage()"
                            ></textarea>
                            <div class="flex items-center justify-between">
                                <x-filament::button
                                    type="submit"
                                    icon="heroicon-o-paper-airplane"
                                    color="primary"
                                    wire:loading.attr="disabled"
                                    wire:target="sendMessage"
                                >
                                    Senden
                                </x-filament::button>
                            </div>
                        </form>
                    </div>
                </x-filament::card>
            </div>

            {{-- Status & Controls (Right Column - 1/3 width) --}}
            <div class="space-y-6">
                {{-- Status Card --}}
                <x-filament::card>
                    <div class="space-y-4">
                        <div>
                            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Agent Status</h4>
                            <div class="flex items-center space-x-2">
                                <span class="h-3 w-3 rounded-full {{ $healthOk ? 'bg-success-500' : 'bg-danger-500' }} animate-pulse"></span>
                                <span class="text-sm text-gray-600 dark:text-gray-400">
                                    {{ $healthOk ? 'Online und bereit' : 'Offline' }}
                                </span>
                            </div>
                        </div>

                        <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
                            <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Session Info</h4>
                            <div class="space-y-2 text-sm">
                                <div>
                                    <span class="text-gray-500 dark:text-gray-400">Session ID:</span>
                                    <p class="text-gray-900 dark:text-gray-100 font-mono text-xs break-all">{{ $sessionId }}</p>
                                </div>
                                <div>
                                    <span class="text-gray-500 dark:text-gray-400">Nachrichten:</span>
                                    <p class="text-gray-900 dark:text-gray-100 font-semibold">{{ count($messages) }}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </x-filament::card>

                {{-- Action Buttons Card --}}
                <x-filament::card>
                    <div class="space-y-3">
                        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Aktionen</h4>
                        
                        <x-filament::button
                            wire:click="refreshMessages"
                            icon="heroicon-o-arrow-path"
                            color="secondary"
                            class="w-full"
                            outlined
                        >
                            Aktualisieren
                        </x-filament::button>

                        <x-filament::button
                            wire:click="clearHistory"
                            icon="heroicon-o-trash"
                            color="danger"
                            class="w-full"
                            outlined
                        >
                            Verlauf löschen
                        </x-filament::button>
                    </div>
                </x-filament::card>

                {{-- Help Card --}}
                <x-filament::card>
                    <div class="space-y-2">
                        <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Tipps</h4>
                        <ul class="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                            <li class="flex items-start">
                                <x-filament::icon icon="heroicon-m-check" class="h-3 w-3 mr-1 mt-0.5 text-success-500" />
                                <span>Enter zum Senden</span>
                            </li>
                            <li class="flex items-start">
                                <x-filament::icon icon="heroicon-m-check" class="h-3 w-3 mr-1 mt-0.5 text-success-500" />
                                <span>Shift+Enter für neue Zeile</span>
                            </li>
                            <li class="flex items-start">
                                <x-filament::icon icon="heroicon-m-check" class="h-3 w-3 mr-1 mt-0.5 text-success-500" />
                                <span>Markdown wird unterstützt</span>
                            </li>
                        </ul>
                    </div>
                </x-filament::card>
            </div>
        </div>
    @else
        {{-- Offline State --}}
        <div class="flex items-center justify-center min-h-[400px]">
            <x-filament::card class="max-w-md">
                <div class="text-center p-6">
                    <x-filament::icon icon="heroicon-o-exclamation-triangle" class="h-16 w-16 text-warning-500 mx-auto mb-4" />
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">AI Agent ist offline</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                        Der AI Agent ist momentan nicht verfügbar. Bitte versuchen Sie es später erneut.
                    </p>
                    <x-filament::button
                        wire:click="$refresh"
                        icon="heroicon-o-arrow-path"
                        color="secondary"
                    >
                        Erneut versuchen
                    </x-filament::button>
                </div>
            </x-filament::card>
        </div>
    @endif

    @push('scripts')
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script>
            function aiChatPage() {
                return {
                    isStreaming: false,
                    controller: null,
                    init() {
                        window.addEventListener('chat:streaming-start', (e) => {
                            this.startStreaming(e.detail.sessionId, e.detail.message);
                        });

                        // Scroll to bottom on mount
                        this.scrollToBottom();
                    },
                    scrollToBottom() {
                        this.$nextTick(() => {
                            const container = this.$refs.messagesContainer;
                            if (container) {
                                container.scrollTop = container.scrollHeight;
                            }
                        });
                    },
                    startStreaming(sessionId, message) {
                        this.isStreaming = true;
                        if (this.controller) {
                            this.controller.abort();
                        }
                        this.controller = new AbortController();
                        const signal = this.controller.signal;
                        const streamingDiv = this.$refs.streamingMessage;
                        let fullResponse = '';

                        const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

                        fetch('/kradmin/ai-chat/stream', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                ...(csrf ? { 'X-CSRF-TOKEN': csrf } : {}),
                            },
                            body: JSON.stringify({
                                session_id: sessionId,
                                message: message,
                            }),
                            signal,
                        }).then(response => {
                            if (!response.body) {
                                throw new Error('Streaming response body missing');
                            }
                            const reader = response.body.getReader();
                            const decoder = new TextDecoder();

                            const processChunk = ({ done, value }) => {
                                if (done) {
                                    this.isStreaming = false;
                                    this.$wire.call('refreshMessages');
                                    this.scrollToBottom();
                                    return;
                                }

                                const text = decoder.decode(value, { stream: true });
                                const events = text.split('\n\n').filter(Boolean);

                                events.forEach(event => {
                                    const line = event.replace(/^data:\s*/, '').trim();

                                    if (line === '[DONE]') {
                                        this.isStreaming = false;
                                        this.$wire.call('refreshMessages');
                                        this.scrollToBottom();
                                        return;
                                    }

                                    try {
                                        const data = JSON.parse(line);
                                        if (data.chunk) {
                                            fullResponse += data.chunk;
                                            if (streamingDiv) {
                                                const parsed = marked.parse(fullResponse);
                                                streamingDiv.querySelector('.bg-gray-100, .dark\\:bg-gray-800').innerHTML = 
                                                    '<div class="text-sm prose dark:prose-invert prose-sm max-w-none">' + parsed + '</div>';
                                            }
                                            this.scrollToBottom();
                                        }
                                        if (data.error) {
                                            console.error('Streaming error:', data.error);
                                            this.isStreaming = false;
                                            this.$wire.call('fallbackChat', message);
                                        }
                                    } catch (e) {
                                        console.error('Parse error:', e);
                                    }
                                });

                                return reader.read().then(processChunk);
                            };

                            return reader.read().then(processChunk);
                        }).catch(error => {
                            if (signal.aborted) return;
                            console.error('Streaming failed:', error);
                            this.isStreaming = false;
                            this.$wire.call('fallbackChat', message);
                        });
                    },
                };
            }
        </script>
    @endpush
</x-filament-panels::page>

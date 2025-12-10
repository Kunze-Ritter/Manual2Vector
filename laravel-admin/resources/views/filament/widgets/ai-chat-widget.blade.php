<div
    x-data="aiChatWidget()"
    x-init="init()"
    @keydown.escape.window="open = false"
    class="fixed inset-0 z-50 pointer-events-none"
>
    <div
        x-show="!open"
        x-transition
        class="pointer-events-auto fixed bottom-6 right-6 z-50"
    >
        <x-filament::button
            icon="heroicon-o-chat-bubble-left-right"
            color="primary"
            size="lg"
            class="rounded-full shadow-lg hover:scale-105 transition-transform"
            @click="open = !open"
        >
            AI Chat
            @php
                $health = $this->getAgentHealth();
                $healthOk = $health['success'] ?? false;
            @endphp
            <span
                class="ml-2 h-2 w-2 rounded-full {{ $healthOk ? 'bg-success-500' : 'bg-danger-500' }}"
            ></span>
        </x-filament::button>
    </div>

    <div
        x-show="open"
        x-transition:enter="transform transition ease-out duration-300"
        x-transition:enter-start="translate-x-full"
        x-transition:enter-end="translate-x-0"
        x-transition:leave="transform transition ease-in duration-200"
        x-transition:leave-start="translate-x-0"
        x-transition:leave-end="translate-x-full"
        class="pointer-events-auto fixed top-0 right-0 h-full w-full md:w-96 lg:w-[28rem] z-50 bg-white dark:bg-gray-900 shadow-2xl border-l border-gray-200 dark:border-gray-700 flex flex-col"
    >
        <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center space-x-2">
                <x-filament::icon icon="heroicon-o-sparkles" class="h-5 w-5 text-primary-500" />
                <div>
                    <p class="text-sm font-semibold text-gray-900 dark:text-gray-100">KRAI AI Assistant</p>
                    @php
                        $health = $this->getAgentHealth();
                        $healthOk = $health['success'] ?? false;
                    @endphp
                    <x-filament::badge :color="$healthOk ? 'success' : 'danger'" size="sm">
                        {{ $healthOk ? 'Online' : 'Offline' }}
                    </x-filament::badge>
                </div>
            </div>
            <x-filament::icon-button
                icon="heroicon-o-x-mark"
                label="Schließen"
                color="secondary"
                @click="open = false"
                class="rounded-full"
            />
        </div>

        @php
            $health = $this->getAgentHealth();
            $healthOk = $health['success'] ?? false;
        @endphp

        @if($healthOk)
            <div class="flex-1 overflow-y-auto p-4 space-y-4" x-ref="messagesContainer">
                @foreach($messages as $message)
                    @if(($message['role'] ?? '') === 'user')
                        <div class="flex justify-end">
                            <div class="bg-primary-100 dark:bg-primary-900 text-primary-900 dark:text-primary-100 rounded-lg p-3 max-w-[80%] ml-auto">
                                <p class="text-sm whitespace-pre-line">{{ $message['content'] ?? '' }}</p>
                                <p class="text-[11px] text-gray-500 mt-1">{{ \Carbon\Carbon::parse($message['timestamp'] ?? now())->format('H:i') }}</p>
                            </div>
                        </div>
                    @else
                        <div class="flex justify-start">
                            <div class="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg p-3 max-w-[80%]">
                                <p class="text-sm prose dark:prose-invert">{!! \Illuminate\Support\Str::markdown($message['content'] ?? '') !!}</p>
                                <p class="text-[11px] text-gray-500 mt-1">{{ \Carbon\Carbon::parse($message['timestamp'] ?? now())->format('H:i') }}</p>
                            </div>
                        </div>
                    @endif
                @endforeach

                <div
                    x-show="isStreaming"
                    x-ref="streamingMessage"
                    class="flex justify-start"
                >
                    <div class="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg p-3 max-w-[80%]">
                        <div class="flex space-x-1">
                            <span class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></span>
                            <span class="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.15s]"></span>
                            <span class="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0.3s]"></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4">
                <form wire:submit.prevent="sendMessage" class="space-y-3">
                    <textarea
                        wire:model.defer="currentMessage"
                        rows="2"
                        placeholder="Frage stellen..."
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
                        <x-filament::button
                            type="button"
                            color="danger"
                            icon="heroicon-o-trash"
                            size="sm"
                            wire:click="clearHistory"
                        >
                            Verlauf löschen
                        </x-filament::button>
                    </div>
                </form>
            </div>
        @else
            <div class="flex-1 flex items-center justify-center text-center p-6">
                <div>
                    <x-filament::icon icon="heroicon-o-exclamation-triangle" class="h-12 w-12 text-warning-500 mx-auto mb-2" />
                    <p class="text-sm text-gray-600 dark:text-gray-300">AI Agent ist offline</p>
                </div>
            </div>
        @endif
    </div>
</div>

@push('scripts')
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        function aiChatWidget() {
            return {
                open: @entangle('isOpen'),
                isStreaming: false,
                controller: null,
                init() {
                    this.$watch('open', (value) => {
                        if (value) this.scrollToBottom();
                    });

                    window.addEventListener('chat:streaming-start', (e) => {
                        this.startStreaming(e.detail.sessionId, e.detail.message);
                    });
                },
                scrollToBottom() {
                    this.$nextTick(() => {
                        const container = this.$refs.messagesContainer;
                        if (container) container.scrollTop = container.scrollHeight;
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
                                            streamingDiv.innerHTML = marked.parse(fullResponse);
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

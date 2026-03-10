<x-filament-panels::page>
    @php
        $health = $this->getAgentHealth();
        $healthOk = $health['success'] ?? false;
    @endphp

    @if($healthOk)
        <div class="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-4 h-[calc(100vh-10rem)]">
            <aside class="bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
                <div class="p-4 border-b border-gray-200 dark:border-gray-700">
                    <x-filament::button wire:click="newChat" icon="heroicon-o-plus" class="w-full" color="primary">
                        Neuer Chat
                    </x-filament::button>
                </div>

                <div class="px-4 pt-4 pb-2">
                    <p class="text-xs uppercase tracking-wide text-gray-500 dark:text-gray-400">Sessions</p>
                </div>

                <div class="flex-1 overflow-y-auto px-2 pb-3 space-y-1">
                    @forelse($chatSessions as $chatSession)
                        @php
                            $isActive = ($chatSession['session_key'] ?? '') === ($sessionId ?? '');
                            $title = $chatSession['title'] ?: 'Unbenannter Chat';
                        @endphp
                        <div class="group rounded-lg {{ $isActive ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800' : 'hover:bg-gray-50 dark:hover:bg-gray-800/60 border border-transparent' }}">
                            <button
                                wire:click="switchSession('{{ $chatSession['session_key'] }}')"
                                class="w-full text-left px-3 py-2"
                            >
                                <p class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{{ $title }}</p>
                                <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{{ \Carbon\Carbon::parse($chatSession['last_active'] ?? now())->format('d.m.Y H:i') }}</p>
                            </button>
                            <div class="px-3 pb-2">
                                <button
                                    wire:click.stop="deleteSession('{{ $chatSession['session_key'] }}')"
                                    class="text-xs text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                                    title="Session loeschen"
                                >
                                    Loeschen
                                </button>
                            </div>
                        </div>
                    @empty
                        <p class="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">Noch keine Sessions vorhanden.</p>
                    @endforelse
                </div>

                <div class="p-3 border-t border-gray-200 dark:border-gray-700">
                    <div class="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                        <p class="font-medium">Slash Commands</p>
                        <p><code>/help</code> <code>/errors</code> <code>/products</code> <code>/docs</code> <code>/stats</code></p>
                    </div>
                </div>
            </aside>

            <section class="bg-white dark:bg-gray-900 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 flex flex-col overflow-hidden">
                <div class="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white">
                    <div class="flex items-center gap-3">
                        <div class="relative">
                            <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                                <x-filament::icon icon="heroicon-o-sparkles" class="w-5 h-5" />
                            </div>
                            <span class="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-primary-600 rounded-full"></span>
                        </div>
                        <div>
                            <h2 class="font-semibold text-white">KRAI AI Workspace</h2>
                            <p class="text-xs text-white/80 truncate">{{ $sessionTitle ?: 'Aktive Session' }}</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-1">
                        <button wire:click="clearHistory" class="p-2 hover:bg-white/10 rounded-full transition" title="Chat loeschen">
                            <x-filament::icon icon="heroicon-o-trash" class="w-5 h-5" />
                        </button>
                        <button wire:click="$refresh" class="p-2 hover:bg-white/10 rounded-full transition" title="Aktualisieren">
                            <x-filament::icon icon="heroicon-o-arrow-path" class="w-5 h-5" />
                        </button>
                    </div>
                </div>

                <div class="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-800" wire:poll.8s>
                    <div class="h-full overflow-y-auto p-4 space-y-4" x-ref="chatContainer">
                        @if(count($messages) === 0)
                            <div class="flex justify-center py-8">
                                <div class="text-center max-w-xl">
                                    <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900 dark:to-primary-800 flex items-center justify-center">
                                        <x-filament::icon icon="heroicon-o-sparkles" class="w-10 h-10 text-primary-600 dark:text-primary-400" />
                                    </div>
                                    <h3 class="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Agent Chat wie OpenWebUI</h3>
                                    <p class="text-gray-600 dark:text-gray-400 mb-4">Nutze freie Fragen oder Slash-Commands fuer strukturierte Daten aus der DB.</p>
                                    <div class="flex flex-wrap justify-center gap-2">
                                        <button wire:click="$set('currentMessage', '/help')" class="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-full hover:border-primary-500 hover:text-primary-600 transition">
                                            /help
                                        </button>
                                        <button wire:click="$set('currentMessage', '/errors 13.B9 5')" class="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-full hover:border-primary-500 hover:text-primary-600 transition">
                                            /errors
                                        </button>
                                        <button wire:click="$set('currentMessage', '/products printer 5')" class="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-full hover:border-primary-500 hover:text-primary-600 transition">
                                            /products
                                        </button>
                                        <button wire:click="$set('currentMessage', '/stats')" class="px-4 py-2 text-sm bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-full hover:border-primary-500 hover:text-primary-600 transition">
                                            /stats
                                        </button>
                                    </div>
                                </div>
                            </div>
                        @endif

                        @foreach($messages as $index => $message)
                            @if(($message['role'] ?? '') === 'user')
                                <div class="flex justify-end">
                                    <div class="flex items-end gap-2 max-w-[80%]">
                                        <div class="bg-primary-500 text-white rounded-2xl rounded-br-sm px-4 py-2.5 shadow-md">
                                            <p class="text-sm whitespace-pre-wrap">{{ $message['content'] ?? '' }}</p>
                                            <p class="text-[10px] text-white/60 text-right mt-1">
                                                {{ \Carbon\Carbon::parse($message['timestamp'] ?? now())->format('H:i') }}
                                            </p>
                                        </div>
                                        <div class="w-8 h-8 rounded-full bg-primary-400 flex items-center justify-center flex-shrink-0">
                                            <x-filament::icon icon="heroicon-o-user" class="w-4 h-4 text-white" />
                                        </div>
                                    </div>
                                </div>
                            @else
                                <div class="flex justify-start">
                                    <div class="flex items-end gap-2 max-w-[85%]">
                                        <div class="w-9 h-9 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center flex-shrink-0">
                                            <x-filament::icon icon="heroicon-o-sparkles" class="w-4 h-4 text-white" />
                                        </div>
                                        <div class="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-2xl rounded-bl-sm px-4 py-2.5 shadow-sm">
                                            <div class="prose dark:prose-invert prose-sm max-w-none">
                                                {!! \Illuminate\Support\Str::markdown($message['content'] ?? '', ['html_input' => 'strip', 'allow_unsafe_links' => false]) !!}
                                            </div>
                                            <p class="text-[10px] text-gray-400 mt-1">
                                                {{ \Carbon\Carbon::parse($message['timestamp'] ?? now())->format('H:i') }}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            @endif
                        @endforeach
                    </div>
                </div>

                <div class="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-3">
                    <div class="flex flex-wrap gap-2 mb-2">
                        <button wire:click="$set('currentMessage', '/help')" class="px-2.5 py-1 text-xs rounded-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary-500">/help</button>
                        <button wire:click="$set('currentMessage', '/errors 13.B9 5')" class="px-2.5 py-1 text-xs rounded-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary-500">/errors</button>
                        <button wire:click="$set('currentMessage', '/products printer 5')" class="px-2.5 py-1 text-xs rounded-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary-500">/products</button>
                        <button wire:click="$set('currentMessage', '/docs service manual 5')" class="px-2.5 py-1 text-xs rounded-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary-500">/docs</button>
                        <button wire:click="$set('currentMessage', '/stats')" class="px-2.5 py-1 text-xs rounded-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary-500">/stats</button>
                    </div>

                    <form wire:submit.prevent="sendMessage" class="flex items-end gap-2">
                        <div class="flex-1">
                            <textarea
                                wire:model="currentMessage"
                                rows="1"
                                placeholder="Nachricht oder /command eingeben..."
                                class="w-full block rounded-2xl border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 shadow-sm focus:border-primary-500 focus:ring-primary-500 dark:text-white resize-none py-2.5 px-4"
                                x-data="{ height: '' }"
                                x-on:input="$el.style.height = ''; $el.style.height = Math.min($el.scrollHeight, 160) + 'px'"
                                x-on:keydown.enter.prevent="$wire.sendMessage()"
                            ></textarea>
                        </div>
                        <button
                            type="submit"
                            class="p-2.5 bg-primary-500 hover:bg-primary-600 disabled:bg-gray-300 text-white rounded-full transition shadow-md"
                            wire:loading.attr="disabled"
                            wire:target="sendMessage"
                        >
                            <x-filament::icon icon="heroicon-o-paper-airplane" class="w-5 h-5" />
                        </button>
                    </form>
                </div>
            </section>
        </div>
    @else
        <div class="flex items-center justify-center min-h-[400px]">
            <x-filament::card class="max-w-md">
                <div class="text-center p-6">
                    <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-warning-100 dark:bg-warning-900/30 flex items-center justify-center">
                        <x-filament::icon icon="heroicon-o-exclamation-triangle" class="h-10 w-10 text-warning-600 dark:text-warning-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">AI Agent ist offline</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-6">
                        Der AI Agent ist nicht erreichbar.
                    </p>
                    <x-filament::button wire:click="retryConnection" icon="heroicon-o-arrow-path" color="primary">
                        Erneut versuchen
                    </x-filament::button>
                </div>
            </x-filament::card>
        </div>
    @endif
</x-filament-panels::page>

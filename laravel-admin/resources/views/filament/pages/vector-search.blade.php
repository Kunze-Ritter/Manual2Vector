<x-filament-panels::page>
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
        <div class="lg:col-span-3">
            <x-filament::card>
                <div class="mb-4">
                    <h2 class="text-lg font-semibold">Semantische Suche</h2>
                    <p class="text-sm text-gray-500">Durchsuchen Sie Ihre Dokumente mit natürlicher Sprache</p>
                </div>

                <form wire:submit.prevent="search" class="space-y-4">
                    <div class="flex gap-4">
                        <div class="flex-1">
                            <x-filament::input.wrapper>
                                <x-filament::input
                                    type="text"
                                    wire:model="searchQuery"
                                    placeholder="z.B. 'Drucker zeigt Fehlermeldung an'..."
                                    required
                                />
                            </x-filament::input.wrapper>
                        </div>
                        <x-filament::button type="submit" :disabled="$isSearching">
                            @if($isSearching)
                                <x-filament::loading-indicator class="w-4 h-4 mr-2" />
                            @endif
                            Suchen
                        </x-filament::button>
                    </div>

                    <div class="flex items-center gap-4 text-sm text-gray-600">
                        <div class="flex items-center gap-2">
                            <label for="limit">Ergebnisse:</label>
                            <x-filament::input.wrapper>
                                <x-filament::input
                                    type="number"
                                    wire:model="limit"
                                    min="1"
                                    max="50"
                                    class="w-20"
                                />
                            </x-filament::input.wrapper>
                        </div>
                        @if($searchResults)
                            <button type="button" wire:click="clearResults" class="text-danger-600 hover:text-danger-700">
                                Ergebnisse löschen
                            </button>
                        @endif
                    </div>
                </form>
            </x-filament::card>
        </div>

        <div class="lg:col-span-1">
            <x-filament::card>
                <h3 class="text-sm font-semibold mb-3">Beispielsuchen</h3>
                <div class="space-y-2">
                    @foreach($this->getSearchExamples() as $example)
                        <button
                            type="button"
                            wire:click="searchExample('{{ $example }}')"
                            class="block w-full text-left text-sm px-3 py-2 rounded-md bg-gray-50 hover:bg-gray-100 text-gray-700 transition-colors"
                            {{ $isSearching ? 'disabled' : '' }}
                        >
                            {{ $example }}
                        </button>
                    @endforeach
                </div>
            </x-filament::card>
        </div>
    </div>

    @if($error)
        <x-filament::card class="mb-6">
            <div class="flex items-center gap-3 text-danger-600">
                <x-filament::icon icon="heroicon-o-exclamation-triangle" class="w-5 h-5" />
                <span>{{ is_string($error) ? $error : json_encode($error) }}</span>
            </div>
        </x-filament::card>
    @endif

    @if($searchResults)
        <x-filament::card>
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h2 class="text-lg font-semibold">Suchergebnisse</h2>
                    <p class="text-sm text-gray-500">
                        {{ $totalCount }} Ergebnisse gefunden
                        @if($processingTime)
                            • {{ round($processingTime) }}ms
                        @endif
                    </p>
                </div>
            </div>

            @if(count($searchResults) > 0)
                <div class="space-y-4">
                    @foreach($searchResults as $index => $result)
                        <div class="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                            <div class="flex items-start justify-between mb-2">
                                <div class="flex-1">
                                    @php
                                        $title = $result['title'] ?? $result['chunk_title'] ?? 'Dokument ' . ($index + 1);
                                        $docType = $result['document_type'] ?? $result['type'] ?? 'unbekannt';
                                        $similarity = $result['similarity'] ?? $result['similarity_score'] ?? null;
                                    @endphp
                                    <h3 class="font-semibold text-gray-900">{{ $title }}</h3>
                                    <div class="flex items-center gap-3 mt-1">
                                        <x-filament::badge color="primary">
                                            {{ $docType }}
                                        </x-filament::badge>
                                        @if($similarity !== null)
                                            <x-filament::badge color="{{ $similarity > 0.7 ? 'success' : ($similarity > 0.5 ? 'warning' : 'gray') }}">
                                                Ähnlichkeit: {{ round($similarity * 100) }}%
                                            </x-filament::badge>
                                        @endif
                                        @if(isset($result['page_number']))
                                            <span class="text-sm text-gray-500">Seite {{ $result['page_number'] }}</span>
                                        @endif
                                    </div>
                                </div>
                            </div>

                            @php
                                $content = $result['content'] ?? $result['text_chunk'] ?? $result['text'] ?? '';
                            @endphp
                            @if($content)
                                <div class="mt-3 p-3 bg-gray-50 rounded text-sm text-gray-700">
                                    {{ \Illuminate\Support\Str::limit($content, 500) }}
                                </div>
                            @endif

                            @php
                                $metadata = $result['metadata'] ?? [];
                            @endphp
                            @if(is_array($metadata) && count($metadata) > 0)
                                <div class="mt-3 flex flex-wrap gap-2">
                                    @foreach($metadata as $key => $value)
                                        @if(is_string($value) && strlen($value) < 50)
                                            <x-filament::badge color="gray">
                                                {{ $key }}: {{ $value }}
                                            </x-filament::badge>
                                        @endif
                                    @endforeach
                                </div>
                            @endif
                        </div>
                    @endforeach
                </div>
            @else
                <div class="text-center py-8 text-gray-500">
                    <x-filament::icon icon="heroicon-o-document-magnifying-glass" class="w-12 h-12 mx-auto mb-3 text-gray-400" />
                    <p>Keine Ergebnisse für Ihre Suchanfrage gefunden.</p>
                </div>
            @endif
        </x-filament::card>
    @elseif(!$isSearching && !$error)
        <x-filament::card>
            <div class="text-center py-12">
                <x-filament::icon icon="heroicon-o-magnifying-glass" class="w-16 h-16 mx-auto mb-4 text-gray-300" />
                <h3 class="text-lg font-semibold text-gray-700 mb-2">Semantische Suche</h3>
                <p class="text-gray-500 max-w-md mx-auto">
                    Geben Sie einen Suchbegriff ein, um Dokumente, Fehlercodes und andere Inhalte
                    basierend auf deren Bedeutung zu durchsuchen.
                </p>
            </div>
        </x-filament::card>
    @endif
</x-filament-panels::page>

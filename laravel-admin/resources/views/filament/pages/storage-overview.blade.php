<x-filament::page>
    <div class="space-y-6" wire:init="loadImages" wire:poll.{{ $pollingInterval }}>
        {{-- Stats --}}
        <x-filament::section>
            <x-slot name="heading">
                Object Storage
            </x-slot>
            <x-slot name="description">
                Übersicht über alle im Object Storage gespeicherten Medien (Bilder aus den Dokumenten).
            </x-slot>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <p class="text-sm text-gray-500">Anzahl Objekte</p>
                    <p class="mt-2 text-2xl font-semibold text-gray-900">{{ number_format($stats['total_images'] ?? 0) }}</p>
                </div>
                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <p class="text-sm text-gray-500">Mit OCR-Text</p>
                    <p class="mt-2 text-2xl font-semibold text-gray-900">{{ number_format($stats['with_ocr_text'] ?? 0) }}</p>
                </div>
                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <p class="text-sm text-gray-500">Mit AI-Beschreibung</p>
                    <p class="mt-2 text-2xl font-semibold text-gray-900">{{ number_format($stats['with_ai_description'] ?? 0) }}</p>
                </div>
                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <p class="text-sm text-gray-500">Dokumente mit Bildern</p>
                    <p class="mt-2 text-2xl font-semibold text-gray-900">{{ number_format(($stats['by_document'] ?? []) ? count($stats['by_document']) : 0) }}</p>
                </div>
            </div>
        </x-filament::section>

        {{-- Filters --}}
        <x-filament::section>
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                    <x-filament::input.wrapper>
                        <x-filament::input.label value="Dokument" />
                        <select wire:model="filterDocument" class="filament-forms-select-component w-full">
                            <option value="">Alle</option>
                            @foreach ($documents as $doc)
                                <option value="{{ $doc->id }}">{{ $doc->filename }}</option>
                            @endforeach
                        </select>
                    </x-filament::input.wrapper>
                </div>
                <div>
                    <x-filament::input.wrapper>
                        <x-filament::input.label value="Datum von" />
                        <x-filament::input type="date" wire:model="filterDateFrom" />
                    </x-filament::input.wrapper>
                </div>
                <div>
                    <x-filament::input.wrapper>
                        <x-filament::input.label value="Datum bis" />
                        <x-filament::input type="date" wire:model="filterDateTo" />
                    </x-filament::input.wrapper>
                </div>
                <div>
                    <x-filament::input.wrapper>
                        <x-filament::input.label value="Suche" />
                        <x-filament::input type="text" placeholder="Dateiname, OCR, AI..." wire:model.debounce.500ms="filterSearch" />
                    </x-filament::input.wrapper>
                </div>
                <div>
                    <x-filament::input.wrapper>
                        <x-filament::input.label value="Dateigröße min (MB)" />
                        <x-filament::input type="number" wire:model="filterFileSizeMin" min="0" step="1" />
                    </x-filament::input.wrapper>
                </div>
                <div>
                    <x-filament::input.wrapper>
                        <x-filament::input.label value="Dateigröße max (MB)" />
                        <x-filament::input type="number" wire:model="filterFileSizeMax" min="0" step="1" />
                    </x-filament::input.wrapper>
                </div>
                <div class="flex items-end gap-2">
                    <x-filament::button wire:click="applyFilters" color="primary">Filter anwenden</x-filament::button>
                    <x-filament::button wire:click="resetFilters" color="gray">Reset</x-filament::button>
                </div>
            </div>
        </x-filament::section>

        {{-- Charts --}}
        <x-filament::section>
            @php
                $totalImages = $stats['total_images'] ?? 0;
                $byType = $stats['by_type'] ?? [];
                $byDocument = $stats['by_document'] ?? [];
            @endphp
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                    <h3 class="text-sm font-semibold text-gray-700 mb-3">Verteilung nach Bildtyp</h3>
                    <div class="space-y-2">
                        @forelse ($byType as $type => $count)
                            @php
                                $ratio = $totalImages > 0 ? ($count / $totalImages) * 100 : 0;
                            @endphp
                            <div>
                                <div class="flex items-center justify-between text-xs text-gray-600">
                                    <span>{{ ucfirst($type) }}</span>
                                    <span>{{ $count }} ({{ number_format($ratio, 1) }}%)</span>
                                </div>
                                <div class="w-full h-2 bg-gray-100 rounded">
                                    <div class="h-2 bg-primary-500 rounded" style="width: {{ $ratio }}%"></div>
                                </div>
                            </div>
                        @empty
                            <div class="text-sm text-gray-500">Keine Typ-Daten vorhanden.</div>
                        @endforelse
                    </div>
                </div>
                <div>
                    <h3 class="text-sm font-semibold text-gray-700 mb-3">Top Dokumente mit Bildern</h3>
                    <div class="space-y-2">
                        @php
                            $topDocs = collect($byDocument)->sortDesc()->take(5);
                        @endphp
                        @forelse ($topDocs as $docId => $count)
                            @php
                                $ratio = $totalImages > 0 ? ($count / $totalImages) * 100 : 0;
                            @endphp
                            <div>
                                <div class="flex items-center justify-between text-xs text-gray-600">
                                    <a href="{{ route('filament.kradmin.resources.documents.edit', $docId) }}" class="text-primary-600 hover:underline">
                                        {{ $docId }}
                                    </a>
                                    <span>{{ $count }} ({{ number_format($ratio, 1) }}%)</span>
                                </div>
                                <div class="w-full h-2 bg-gray-100 rounded">
                                    <div class="h-2 bg-amber-500 rounded" style="width: {{ $ratio }}%"></div>
                                </div>
                            </div>
                        @empty
                            <div class="text-sm text-gray-500">Keine Dokument-Daten vorhanden.</div>
                        @endforelse
                    </div>
                </div>
            </div>
        </x-filament::section>

        {{-- Bulk actions --}}
        <div class="flex flex-wrap items-center gap-3">
            <x-filament::button wire:click="selectAll" color="gray">Alle auswählen</x-filament::button>
            <x-filament::button wire:click="deselectAll" color="gray">Auswahl aufheben</x-filament::button>
            <x-filament::button wire:click="deleteSelected" color="danger">Ausgewählte löschen</x-filament::button>
            <x-filament::button wire:click="downloadSelected" color="primary">Ausgewählte herunterladen</x-filament::button>
            <div class="text-sm text-gray-600">Ausgewählt: {{ count($selectedImages) }}</div>
        </div>

        {{-- Image grid/table --}}
        <div
            x-data="{
                init() {
                    const observer = new IntersectionObserver((entries) => {
                        entries.forEach((entry) => {
                            if (entry.isIntersecting) {
                                $wire.call('loadMore');
                            }
                        });
                    }, { rootMargin: '200px' });
                    observer.observe(this.$refs.loadMoreSentinel);
                }
            }"
            class="space-y-4"
        >
            @unless($imagesLoaded)
                <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
                    @for ($i = 0; $i < 6; $i++)
                        <div class="border border-gray-200 rounded-lg overflow-hidden bg-white animate-pulse">
                            <div class="h-48 bg-gray-100"></div>
                            <div class="p-3 space-y-2">
                                <div class="h-4 bg-gray-100 rounded w-3/4"></div>
                                <div class="h-4 bg-gray-100 rounded w-1/2"></div>
                                <div class="h-4 bg-gray-100 rounded w-2/3"></div>
                            </div>
                        </div>
                    @endfor
                </div>
            @endunless

            <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
                @forelse ($images as $image)
                    <div class="border border-gray-200 rounded-lg overflow-hidden bg-white">
                        <div class="flex items-center justify-between p-3 border-b border-gray-100">
                            <label class="flex items-center gap-2 text-sm text-gray-700">
                                <input type="checkbox" wire:model="selectedImages" value="{{ $image['id'] ?? '' }}" class="rounded border-gray-300 text-primary-600 focus:ring-primary-500">
                                <span class="font-semibold truncate">{{ $image['original_filename'] ?? $image['filename'] ?? 'n/a' }}</span>
                            </label>
                            <x-filament::badge color="gray">{{ $image['image_type'] ?? 'n/a' }}</x-filament::badge>
                        </div>
                        @if (!empty($image['storage_url']))
                            <img src="{{ $image['storage_url'] }}" alt="{{ $image['original_filename'] ?? $image['filename'] ?? '' }}" class="w-full h-48 object-cover">
                        @else
                            <div class="w-full h-48 bg-gray-100 flex items-center justify-center text-gray-400 text-sm">Kein Bild</div>
                        @endif
                        <div class="p-3 space-y-2 text-sm text-gray-700">
                            <div class="flex items-center justify-between">
                                <span class="text-gray-500">Dateiname</span>
                                <span class="font-mono text-xs">{{ $image['filename'] ?? 'n/a' }}</span>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-gray-500">Größe</span>
                                <span>{{ isset($image['file_size']) ? number_format($image['file_size'] / 1024 / 1024, 2) . ' MB' : 'n/a' }}</span>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-gray-500">Seite</span>
                                <span>{{ $image['page_number'] ?? '–' }}</span>
                            </div>
                            <div class="flex items-center justify-between">
                                <span class="text-gray-500">Erstellt</span>
                                <span>{{ $image['created_at'] ?? 'n/a' }}</span>
                            </div>
                            @if (!empty($image['document_id']))
                                <div class="flex items-center justify-between">
                                    <span class="text-gray-500">Dokument</span>
                                    <a href="{{ route('filament.kradmin.resources.documents.edit', $image['document_id']) }}" class="text-primary-600 hover:underline">
                                        {{ $image['document_id'] }}
                                    </a>
                                </div>
                            @endif
                        </div>
                    </div>
                @empty
                    @if($imagesLoaded)
                        <div class="col-span-3 text-sm text-gray-500">Keine Bilder gefunden.</div>
                    @endif
                @endforelse
            </div>

            @if ($totalPages > 1)
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <x-filament::button wire:click="changePage({{ max(1, $page - 1) }})" color="gray" :disabled="$page <= 1">Zurück</x-filament::button>
                        <span class="text-sm text-gray-600">Seite {{ $page }} von {{ $totalPages }}</span>
                        <x-filament::button wire:click="changePage({{ min($totalPages, $page + 1) }})" color="gray" :disabled="$page >= $totalPages">Weiter</x-filament::button>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-sm text-gray-600">Pro Seite</span>
                        <x-filament::input type="number" min="1" max="{{ config('krai.images.max_page_size') }}" wire:model.lazy="pageSize" class="w-24" />
                    </div>
                </div>
            @endif

            @if ($imagesLoaded && $page < $totalPages)
                <div class="text-center text-sm text-gray-500" x-ref="loadMoreSentinel">
                    Mehr laden …
                </div>
            @endif
        </div>
    </div>
</x-filament::page>

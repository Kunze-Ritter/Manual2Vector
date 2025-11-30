<x-filament::page>
    <div class="space-y-6">
        <x-filament::section>
            <x-slot name="heading">
                Object Storage
            </x-slot>

            <x-slot name="description">
                Übersicht über alle im Object Storage gespeicherten Medien (Bilder aus den Dokumenten).
            </x-slot>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <p class="text-sm text-gray-500">Anzahl Objekte</p>
                    <p class="mt-2 text-2xl font-semibold text-gray-900">{{ number_format($totalImages) }}</p>
                </div>

                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <p class="text-sm text-gray-500">Gesamtgröße</p>
                    <p class="mt-2 text-2xl font-semibold text-gray-900">{{ $totalSize }}</p>
                </div>

                <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <p class="text-sm text-gray-500">Dokumente mit Bildern</p>
                    <p class="mt-2 text-2xl font-semibold text-gray-900">{{ number_format($documentsWithImages) }}</p>
                </div>
            </div>
        </x-filament::section>

        <div class="text-xs text-gray-500">
            <p>Quelle: krai_content.images (Object Storage Index)</p>
        </div>
    </div>
</x-filament::page>

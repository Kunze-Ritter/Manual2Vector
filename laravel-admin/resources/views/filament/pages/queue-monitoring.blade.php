<x-filament::page>
    <div class="space-y-6">
        @if (!($queueData['success'] ?? false))
            <div class="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 flex items-start gap-3">
                <x-filament::icon icon="heroicon-o-exclamation-triangle" class="h-6 w-6 text-red-500" />
                <div>
                    <div class="font-semibold">Fehler beim Laden der Warteschlange</div>
                    <div class="text-sm">{{ $queueData['error'] ?? 'Unbekannter Fehler' }}</div>
                </div>
            </div>
        @else
            @php
                $metrics = $queueData['queue_metrics'] ?? [];
                $items = $queueData['queue_items'] ?? [];
                $completed = (int) ($metrics['completed_count'] ?? 0);
                $processing = (int) ($metrics['processing_count'] ?? 0);
                $total = max(1, $completed + $processing + (int) ($metrics['pending_count'] ?? 0));
                $progress = min(100, max(0, ($completed / $total) * 100));
            @endphp

            <x-filament::section heading="Warteschlangen-Metriken">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">Pending</div>
                        <div class="font-semibold text-blue-600">
                            {{ $metrics['pending_count'] ?? 0 }}
                        </div>
                        <div class="text-xs text-gray-500">
                            Ø Wartezeit: {{ $metrics['avg_wait_time_seconds'] ?? 0 }}s
                        </div>
                    </div>
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">In Bearbeitung</div>
                        <div class="font-semibold text-amber-600">
                            {{ $metrics['processing_count'] ?? 0 }}
                        </div>
                        <div class="text-xs text-gray-500">
                            Aktive Worker: {{ $metrics['active_workers'] ?? 'n/a' }}
                        </div>
                    </div>
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">Abgeschlossen</div>
                        <div class="font-semibold text-green-600">
                            {{ $metrics['completed_count'] ?? 0 }}
                        </div>
                        <div class="text-xs text-gray-500">
                            Erfolgsrate: {{ number_format((float) ($metrics['success_rate'] ?? 0), 1) }}%
                        </div>
                    </div>
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">Fehlgeschlagen</div>
                        <div class="font-semibold text-red-600">
                            {{ $metrics['failed_count'] ?? 0 }}
                        </div>
                        @if (!empty($metrics['top_failure_types']))
                            <div class="mt-2 text-xs text-gray-600 space-y-1">
                                @foreach ($metrics['top_failure_types'] as $type => $count)
                                    <div class="flex justify-between">
                                        <span class="truncate">{{ $type }}</span>
                                        <span class="font-semibold">{{ $count }}</span>
                                    </div>
                                @endforeach
                            </div>
                        @endif
                    </div>
                </div>
            </x-filament::section>

            <x-filament::section heading="Fortschritt">
                <div class="space-y-3">
                    <div class="w-full h-3 rounded-full bg-gray-200 overflow-hidden">
                        <div class="h-3 bg-gradient-to-r from-blue-400 to-green-500" style="width: {{ $progress }}%"></div>
                    </div>
                    <div class="flex flex-wrap gap-6 text-sm">
                        <div>
                            <div class="text-gray-500">Abgeschlossen</div>
                            <div class="font-semibold text-green-600">{{ $completed }}</div>
                        </div>
                        <div>
                            <div class="text-gray-500">In Bearbeitung</div>
                            <div class="font-semibold text-amber-600">{{ $processing }}</div>
                        </div>
                        <div>
                            <div class="text-gray-500">Ø Wartezeit</div>
                            <div class="font-semibold">{{ $metrics['avg_wait_time_seconds'] ?? 0 }}s</div>
                        </div>
                        <div>
                            <div class="text-gray-500">Ältester Eintrag</div>
                            <div class="font-semibold">
                                @if (!empty($metrics['oldest_item_age_seconds']))
                                    {{ $metrics['oldest_item_age_seconds'] }}s
                                @else
                                    —
                                @endif
                            </div>
                        </div>
                    </div>
                </div>
            </x-filament::section>

            <x-filament::section heading="Aktuelle Einträge">
                <div class="flex items-center gap-2 mb-3">
                    @foreach (['all' => 'Alle', 'pending' => 'Pending', 'processing' => 'Processing', 'failed' => 'Failed'] as $key => $label)
                        <button
                            wire:click="$set('statusFilter','{{ $key }}')"
                            class="px-3 py-1.5 rounded-lg text-sm border {{ $statusFilter === $key ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-white border-gray-200 text-gray-600' }}"
                            type="button"
                        >
                            {{ $label }}
                        </button>
                    @endforeach
                </div>

                @php
                    $filtered = $this->getFilteredItems($items);
                @endphp

                @if (empty($filtered))
                    <div class="text-sm text-gray-500">Warteschlange ist leer.</div>
                @else
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-gray-200 text-sm">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-4 py-2 text-left font-semibold text-gray-700">ID</th>
                                    <th class="px-4 py-2 text-left font-semibold text-gray-700">Aufgabe</th>
                                    <th class="px-4 py-2 text-left font-semibold text-gray-700">Status</th>
                                    <th class="px-4 py-2 text-left font-semibold text-gray-700">Priorität</th>
                                    <th class="px-4 py-2 text-left font-semibold text-gray-700">Retries</th>
                                    <th class="px-4 py-2 text-left font-semibold text-gray-700">Dauer</th>
                                    <th class="px-4 py-2 text-left font-semibold text-gray-700">Geplant</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-100">
                                @foreach ($filtered as $item)
                                    <tr class="hover:bg-gray-50">
                                        <td class="px-4 py-2 font-mono truncate" title="{{ $item['id'] ?? '' }}">
                                            {{ \Illuminate\Support\Str::limit($item['id'] ?? '', 12, '…') }}
                                        </td>
                                        <td class="px-4 py-2">
                                            <x-filament::badge color="gray">
                                                {{ $item['task_type'] ?? 'n/a' }}
                                            </x-filament::badge>
                                        </td>
                                        <td class="px-4 py-2">
                                            <x-filament::badge :color="$this->getStatusBadgeColor($item['status'] ?? '')">
                                                {{ ucfirst($item['status'] ?? 'n/a') }}
                                            </x-filament::badge>
                                        </td>
                                        <td class="px-4 py-2">{{ $item['priority'] ?? '-' }}</td>
                                        <td class="px-4 py-2">{{ $item['retries'] ?? 0 }}</td>
                                        <td class="px-4 py-2">
                                            {{ $this->formatDuration($item['started_at'] ?? null, $item['completed_at'] ?? null) }}
                                        </td>
                                        <td class="px-4 py-2 text-gray-600">
                                            @if (!empty($item['scheduled_at']))
                                                {{ $this->formatRelativeTime($item['scheduled_at']) }}
                                            @else
                                                —
                                            @endif
                                        </td>
                                    </tr>
                                @endforeach
                            </tbody>
                        </table>
                    </div>
                @endif
            </x-filament::section>

            <x-filament::section heading="Verteilung nach Aufgabentyp">
                @if (!empty($metrics['by_task_type']))
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-sm">
                        @foreach ($metrics['by_task_type'] as $type => $count)
                            <div class="p-3 rounded-lg border bg-white flex items-center justify-between">
                                <span class="font-medium">{{ $type }}</span>
                                <span class="text-gray-700 font-semibold">{{ $count }}</span>
                            </div>
                        @endforeach
                    </div>
                @else
                    <div class="text-sm text-gray-500">Keine Aufgaben vorhanden.</div>
                @endif
            </x-filament::section>

            @if (($metrics['failed_count'] ?? 0) > 0)
                <div class="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 text-sm">
                    ⚠️ Es gibt fehlgeschlagene Einträge. Bitte prüfen und erneut anstoßen.
                </div>
            @endif
        @endif
    </div>
</x-filament::page>

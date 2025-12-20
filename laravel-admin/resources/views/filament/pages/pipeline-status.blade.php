<x-filament::page>
    <div class="space-y-6">
        @if (!($pipelineData['success'] ?? false))
            <div class="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 flex items-start gap-3">
                <x-filament::icon icon="heroicon-o-exclamation-triangle" class="h-6 w-6 text-red-500" />
                <div>
                    <div class="font-semibold">Fehler beim Laden des Pipeline-Status</div>
                    <div class="text-sm">{{ $pipelineData['error'] ?? 'Unbekannter Fehler' }}</div>
                </div>
            </div>
        @else
            <x-filament::section heading="Gesamt-Fortschritt">
                @php
                    $metrics = $pipelineData['pipeline_metrics'] ?? [];
                    $progress = $this->calculateProgress($metrics);
                @endphp
                <div class="space-y-4">
                    <div class="w-full h-4 rounded-full bg-gray-200 overflow-hidden">
                        <div class="h-4 bg-gradient-to-r from-green-400 to-emerald-600" style="width: {{ $progress }}%"></div>
                    </div>
                    <div class="flex flex-wrap gap-6 text-sm">
                        <div>
                            <div class="text-gray-500">Abgeschlossen</div>
                            <div class="font-semibold text-green-600">
                                {{ $metrics['documents_completed'] ?? 0 }} / {{ $metrics['total_documents'] ?? 0 }}
                            </div>
                        </div>
                        <div>
                            <div class="text-gray-500">In Verarbeitung</div>
                            <div class="font-semibold text-amber-600">
                                {{ $metrics['documents_processing'] ?? 0 }}
                            </div>
                        </div>
                        <div>
                            <div class="text-gray-500">Erfolgsrate</div>
                            <div class="font-semibold">
                                {{ number_format((float) ($metrics['success_rate'] ?? 0), 1) }}%
                            </div>
                        </div>
                        <div>
                            <div class="text-gray-500">Durchsatz</div>
                            <div class="font-semibold">
                                {{ $metrics['throughput_docs_per_hour'] ?? 0 }} Docs/Std
                            </div>
                        </div>
                        <div>
                            <div class="text-gray-500">Ø Bearbeitungszeit</div>
                            <div class="font-semibold">
                                {{ number_format((float) ($metrics['avg_processing_time_seconds'] ?? 0), 2) }}s
                            </div>
                        </div>
                    </div>
                </div>
            </x-filament::section>

            <x-filament::section heading="Pipeline-Stufen">
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200 text-sm">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-4 py-2 text-left font-semibold text-gray-700">Stufe</th>
                                <th class="px-4 py-2 text-left font-semibold text-gray-700">Status</th>
                                <th class="px-4 py-2 text-left font-semibold text-gray-700">Pending</th>
                                <th class="px-4 py-2 text-left font-semibold text-gray-700">Processing</th>
                                <th class="px-4 py-2 text-left font-semibold text-gray-700">Completed</th>
                                <th class="px-4 py-2 text-left font-semibold text-gray-700">Failed</th>
                                <th class="px-4 py-2 text-left font-semibold text-gray-700">Ø Dauer</th>
                                <th class="px-4 py-2 text-left font-semibold text-gray-700">Erfolgsrate</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">
                            @foreach ($pipelineData['stage_metrics'] ?? [] as $stage)
                                @php
                                    $badge = $this->getStageStatusBadge($stage);
                                @endphp
                                <tr class="hover:bg-gray-50 cursor-pointer">
                                    <td class="px-4 py-2 font-medium">
                                        {{ krai_stage_label($stage['stage_name'] ?? '') }}
                                    </td>
                                    <td class="px-4 py-2">
                                        <x-filament::badge :color="$badge['color']">
                                            {{ $badge['label'] }}
                                        </x-filament::badge>
                                    </td>
                                    <td class="px-4 py-2 text-gray-700">{{ $stage['pending_count'] ?? 0 }}</td>
                                    <td class="px-4 py-2 text-amber-600">{{ $stage['processing_count'] ?? 0 }}</td>
                                    <td class="px-4 py-2 text-green-600">{{ $stage['completed_count'] ?? 0 }}</td>
                                    <td class="px-4 py-2 text-red-600">{{ $stage['failed_count'] ?? 0 }}</td>
                                    <td class="px-4 py-2 text-gray-700">
                                        {{ number_format((float) ($stage['avg_duration_seconds'] ?? 0), 2) }}s
                                    </td>
                                    <td class="px-4 py-2 text-gray-700">
                                        {{ number_format((float) ($stage['success_rate'] ?? 0), 1) }}%
                                    </td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>
            </x-filament::section>

            <x-filament::section heading="Hardware-Status">
                @php
                    $hardware = $pipelineData['hardware_status'] ?? [];
                @endphp
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">CPU</div>
                        <div class="font-semibold">{{ $hardware['cpu_usage_percent'] ?? 0 }}%</div>
                        <div class="mt-2 h-2 rounded-full bg-gray-200">
                            <div class="h-2 rounded-full bg-emerald-500" style="width: {{ min(100, (float) ($hardware['cpu_usage_percent'] ?? 0)) }}%"></div>
                        </div>
                    </div>
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">RAM</div>
                        <div class="font-semibold">{{ $hardware['ram_usage_percent'] ?? 0 }}%</div>
                        <div class="mt-2 h-2 rounded-full bg-gray-200">
                            <div class="h-2 rounded-full bg-blue-500" style="width: {{ min(100, (float) ($hardware['ram_usage_percent'] ?? 0)) }}%"></div>
                        </div>
                        <div class="text-xs text-gray-500 mt-1">
                            Verfügbar: {{ $hardware['ram_available_gb'] ?? 0 }} GB
                        </div>
                    </div>
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">GPU</div>
                        <div class="font-semibold">
                            {{ $hardware['gpu_status'] ?? 'n/a' }}
                        </div>
                    </div>
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">Last Aktualisierung</div>
                        <div class="font-semibold">
                            @if (!empty($hardware['last_updated_at']))
                                {{ date('d.m.Y H:i:s', strtotime($hardware['last_updated_at'])) }}
                            @else
                                —
                            @endif
                        </div>
                    </div>
                </div>
            </x-filament::section>

            <x-filament::section heading="Datenqualität">
                @php
                    $qd = $qualityData['data'] ?? [];
                @endphp
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">Erfolgsrate</div>
                        <div class="font-semibold text-green-600">
                            {{ number_format((float) ($qd['success_rate'] ?? 0), 1) }}%
                        </div>
                    </div>
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">Validierungsfehler</div>
                        <div class="font-semibold text-red-600">
                            {{ $qd['validation_errors'] ?? 0 }}
                        </div>
                        @if (!empty($qd['validation_errors_by_stage']))
                            <div class="mt-2 text-xs text-gray-600 space-y-1">
                                @foreach ($qd['validation_errors_by_stage'] as $stage => $count)
                                    <div class="flex justify-between">
                                        <span>{{ krai_stage_label($stage) }}</span>
                                        <span class="font-semibold">{{ $count }}</span>
                                    </div>
                                @endforeach
                            </div>
                        @endif
                    </div>
                    <div class="p-4 rounded-lg border bg-white">
                        <div class="text-gray-500">Duplikate</div>
                        <div class="font-semibold text-amber-600">
                            {{ $qd['duplicate_documents'] ?? 0 }}
                        </div>
                        @if (!empty($qd['duplicate_document_ids']))
                            <div class="mt-2 text-xs text-gray-600 space-y-1">
                                @foreach ($qd['duplicate_document_ids'] as $docId)
                                    <div class="font-mono truncate">{{ $docId }}</div>
                                @endforeach
                            </div>
                        @endif
                    </div>
                </div>
            </x-filament::section>
        @endif
    </div>
</x-filament::page>

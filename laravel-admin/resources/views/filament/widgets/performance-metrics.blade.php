<x-filament-widgets::widget>
    <x-filament::section>
        <x-slot name="heading">
            Performance Metrics
        </x-slot>
        
        {{-- Render stats cards --}}
        <x-filament-widgets::stats-overview-widget :stats="$this->getCachedStats()" />
        
        {{-- Per-stage breakdown table --}}
        @if(!empty($stages))
            <div class="mt-6">
                <h3 class="text-lg font-semibold mb-3">Per-Stage Performance Breakdown</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead class="bg-gray-50 dark:bg-gray-800">
                            <tr>
                                <th class="px-4 py-2 text-left">Stage</th>
                                <th class="px-4 py-2 text-right">Baseline Avg</th>
                                <th class="px-4 py-2 text-right">Current Avg</th>
                                <th class="px-4 py-2 text-right">P95 (Baseline)</th>
                                <th class="px-4 py-2 text-right">P95 (Current)</th>
                                <th class="px-4 py-2 text-right">Improvement</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                            @foreach($stages as $stage)
                                <tr>
                                    <td class="px-4 py-3 font-medium">{{ $stage['stage_name'] }}</td>
                                    <td class="px-4 py-3 text-right">{{ number_format($stage['baseline_avg_seconds'] ?? 0, 3) }}s</td>
                                    <td class="px-4 py-3 text-right">{{ number_format($stage['current_avg_seconds'] ?? 0, 3) }}s</td>
                                    <td class="px-4 py-3 text-right">{{ number_format($stage['baseline_p95_seconds'] ?? 0, 3) }}s</td>
                                    <td class="px-4 py-3 text-right">{{ number_format($stage['current_p95_seconds'] ?? 0, 3) }}s</td>
                                    <td class="px-4 py-3 text-right">
                                        @php
                                            $improvement = $stage['improvement_percentage'] ?? 0;
                                            $badgeColor = $improvement >= 30 ? 'success' : ($improvement >= 10 ? 'warning' : 'danger');
                                        @endphp
                                        <x-filament::badge :color="$badgeColor">
                                            {{ number_format($improvement, 1) }}%
                                        </x-filament::badge>
                                    </td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>
                </div>
            </div>
        @else
            <div class="mt-6 text-center py-4 text-gray-500">
                No performance baseline data available. Run benchmark suite to establish baselines.
            </div>
        @endif
    </x-filament::section>
</x-filament-widgets::widget>

@php
    $groups = config('krai.stage_groups');
@endphp

<div class="space-y-6">
    @if(empty($stageStatus))
        <div class="text-center py-8">
            <x-filament::icon
                icon="heroicon-o-information-circle"
                class="w-12 h-12 mx-auto text-gray-400 mb-4"
            />
            <p class="text-gray-500">Keine Stage-Informationen verfügbar</p>
        </div>
    @else
        @foreach($groups as $group)
            @php
                $groupStages = collect($stages)->filter(fn($stage) => $stage['group'] === $group);
            @endphp
            
            @if($groupStages->isNotEmpty())
                <div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                        {{ ucfirst($group) }}
                    </h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        @foreach($groupStages as $stageKey => $stage)
                            @php
                                $status = strtolower($stageStatus[$stageKey] ?? 'not_started');
                                $badgeColor = match($status) {
                                    'completed' => 'success',
                                    'failed' => 'danger',
                                    'pending', 'in_progress' => 'warning',
                                    default => 'gray'
                                };
                                $icon = match($status) {
                                    'completed' => 'heroicon-o-check-circle',
                                    'failed' => 'heroicon-o-x-circle',
                                    'pending', 'in_progress' => 'heroicon-o-clock',
                                    default => 'heroicon-o-minus-circle'
                                };
                            @endphp
                            
                            <div class="flex items-start space-x-3 p-4 rounded-lg border-2 border-{{ $badgeColor }}-200 dark:border-{{ $badgeColor }}-800 bg-{{ $badgeColor }}-50 dark:bg-{{ $badgeColor }}-900/20">
                                <x-filament::icon
                                    :icon="$stage['icon']"
                                    class="w-6 h-6 text-{{ $badgeColor }}-600 dark:text-{{ $badgeColor }}-400 flex-shrink-0 mt-0.5"
                                />
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center justify-between mb-1">
                                        <h4 class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                                            {{ $stage['label'] }}
                                        </h4>
                                        <x-filament::badge :color="$badgeColor" size="sm">
                                            {{ ucfirst($status) }}
                                        </x-filament::badge>
                                    </div>
                                    <p class="text-xs text-gray-600 dark:text-gray-400">
                                        {{ $stage['description'] }}
                                    </p>
                                </div>
                            </div>
                        @endforeach
                    </div>
                </div>
            @endif
        @endforeach
        
        <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
            @php
                $total = count($stageStatus);
                $completed = collect($stageStatus)->filter(fn($s) => strtolower($s) === 'completed')->count();
                $failed = collect($stageStatus)->filter(fn($s) => strtolower($s) === 'failed')->count();
                $pending = collect($stageStatus)->filter(fn($s) => in_array(strtolower($s), ['pending', 'in_progress']))->count();
                $progress = $total > 0 ? round(($completed / $total) * 100) : 0;
            @endphp
            
            <div class="flex items-center justify-between text-sm">
                <div class="space-x-4">
                    <span class="text-green-600 dark:text-green-400">✓ {{ $completed }} Abgeschlossen</span>
                    <span class="text-red-600 dark:text-red-400">✗ {{ $failed }} Fehlgeschlagen</span>
                    <span class="text-yellow-600 dark:text-yellow-400">⏳ {{ $pending }} Ausstehend</span>
                </div>
                <div class="text-gray-600 dark:text-gray-400 font-semibold">
                    {{ $progress }}% Fortschritt
                </div>
            </div>
            
            <div class="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div class="bg-green-600 dark:bg-green-500 h-2 rounded-full transition-all duration-300" style="width: {{ $progress }}%"></div>
            </div>
        </div>
    @endif
</div>

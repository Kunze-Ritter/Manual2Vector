@php
    $record = $getRecord();
    $stageStatus = $record->stage_status ?? [];
    $stages = config('krai.stages');
    $groups = config('krai.stage_groups');
@endphp

<div class="space-y-4">
    @foreach($groups as $group)
        @php
            $groupStages = collect($stages)->filter(fn($stage) => $stage['group'] === $group);
        @endphp
        
        @if($groupStages->isNotEmpty())
            <div>
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    {{ ucfirst($group) }}
                </h4>
                
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
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
                        
                        <div class="flex items-center space-x-2 p-2 rounded-lg border border-gray-200 dark:border-gray-700">
                            <x-filament::icon
                                :icon="$icon"
                                class="w-5 h-5 text-{{ $badgeColor }}-500"
                            />
                            <div class="flex-1 min-w-0">
                                <div class="text-xs font-medium text-gray-900 dark:text-gray-100 truncate">
                                    {{ $stage['label'] }}
                                </div>
                                <div class="text-xs text-gray-500 dark:text-gray-400">
                                    {{ ucfirst($status) }}
                                </div>
                            </div>
                        </div>
                    @endforeach
                </div>
            </div>
        @endif
    @endforeach
</div>

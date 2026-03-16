<x-dynamic-component
    :component="$getFieldWrapperView()"
    :field="$field"
>
    @php
        $state = $getState();
    @endphp

    @if(!$state || !is_array($state))
        <div class="text-sm text-gray-500 italic">
            {{ __('Keine Retry-Historie verfügbar') }}
        </div>
    @else
        <div class="space-y-2">
            @foreach($state as $retry)
                @php
                    $timestamp = $retry['timestamp'] ?? 'N/A';
                    $status = $retry['status'] ?? 'unknown';
                    $message = $retry['message'] ?? 'Keine Nachricht';

                    $icon = match ($status) {
                        'success' => '✅',
                        'failed' => '❌',
                        'retrying' => '🔄',
                        default => '⚠️',
                    };

                    $color = match ($status) {
                        'success' => 'text-green-600',
                        'failed' => 'text-red-600',
                        'retrying' => 'text-yellow-600',
                        default => 'text-gray-600',
                    };
                @endphp

                <div class="flex items-start gap-3 p-3 rounded-lg border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                    <span class="text-xl shrink-0">{{ $icon }}</span>
                    <div class="flex-1 min-w-0">
                        <div @class(['font-bold uppercase text-xs tracking-wider', $color])>
                            {{ ucfirst($status) }}
                        </div>
                        <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {{ $timestamp }}
                        </div>
                        <div class="text-sm mt-1.5 break-words">
                            {{ $message }}
                        </div>
                    </div>
                </div>
            @endforeach
        </div>
    @endif
</x-dynamic-component>

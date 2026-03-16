<x-dynamic-component
    :component="$getFieldWrapperView()"
    :field="$field"
>
    @php
        $state = $getState();
        $json = null;
        if ($state) {
            try {
                $json = is_string($state) ? $state : json_encode($state, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
            } catch (\Exception $e) {
                $json = 'Error encoding JSON: ' . $e->getMessage();
            }
        }
    @endphp

    @if(!$json)
        <div class="text-sm text-gray-500 italic">
            {{ __('Kein Context verfügbar') }}
        </div>
    @else
        <div class="p-4 rounded-lg bg-gray-900 text-blue-100 overflow-x-auto border border-gray-800 font-mono text-xs leading-relaxed max-h-96 overflow-y-auto shadow-inner">
            <pre><code>{{ $json }}</code></pre>
        </div>
    @endif
</x-dynamic-component>

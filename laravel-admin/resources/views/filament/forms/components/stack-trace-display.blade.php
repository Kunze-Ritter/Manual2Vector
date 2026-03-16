<x-dynamic-component
    :component="$getFieldWrapperView()"
    :field="$field"
>
    @php
        $state = $getState();
    @endphp

    @if(!$state)
        <div class="text-sm text-gray-500 italic">
            {{ __('Kein Stack Trace verfügbar') }}
        </div>
    @else
        <div class="p-4 rounded-lg bg-gray-950 text-gray-100 overflow-x-auto border border-gray-800 font-mono text-xs leading-relaxed max-h-96 overflow-y-auto">
            <pre><code>{{ $state }}</code></pre>
        </div>
    @endif
</x-dynamic-component>

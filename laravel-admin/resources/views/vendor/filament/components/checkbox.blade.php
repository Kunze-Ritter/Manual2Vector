@props([
    'label' => null,
    'hint' => null,
])

<label class="flex items-start gap-2">
    <input
        type="checkbox"
        {{ $attributes->class('mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500') }}
    />

    @if($label || $hint)
        <span>
            @if($label)
                <span class="block text-sm font-medium text-gray-900">{{ $label }}</span>
            @endif

            @if($hint)
                <span class="block text-xs text-gray-500">{{ $hint }}</span>
            @endif
        </span>
    @endif
</label>

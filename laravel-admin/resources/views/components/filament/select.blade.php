@props([
    'label' => null,
    'hint' => null,
])

<div class="space-y-1">
    @if($label)
        <label class="block text-sm font-medium text-gray-900">
            {{ $label }}
        </label>
    @endif

    <select {{ $attributes->class('block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm') }}>
        {{ $slot }}
    </select>

    @if($hint)
        <p class="mt-1 text-xs text-gray-500">{{ $hint }}</p>
    @endif
</div>

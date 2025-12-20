@php
    $info = $getState() ?? [];
@endphp

<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
        <div class="text-sm text-gray-500 dark:text-gray-400">Version</div>
        <div class="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-50">
            {{ $info['version'] ?? 'Unknown' }}
        </div>
    </div>

    <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
        <div class="text-sm text-gray-500 dark:text-gray-400">Build</div>
        <div class="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-50">
            {{ $info['build'] ?? 'Unknown' }}
        </div>
    </div>

    <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
        <div class="text-sm text-gray-500 dark:text-gray-400">Status</div>
        <div class="mt-1 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-gray-50">
            <span class="inline-flex h-2 w-2 rounded-full {{ ($info['status'] ?? null) === 'online' ? 'bg-green-500' : 'bg-gray-400' }}"></span>
            {{ $info['status'] ?? 'Unknown' }}
        </div>
    </div>

    <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
        <div class="text-sm text-gray-500 dark:text-gray-400">Models</div>
        <div class="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-50">
            {{ $info['model_count'] ?? ($info['models'] ?? null ? count($info['models']) : '0') }}
        </div>
    </div>
</div>

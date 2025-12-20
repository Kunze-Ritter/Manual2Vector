@php
    $models = $getState() ?? [];
@endphp

<div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-900">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-50">Ollama Models</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">Manage local models available to this instance.</p>
        </div>
        <div class="flex flex-wrap gap-2">
            <x-filament::button tag="button" icon="heroicon-o-plus" wire:click="$parent.showPullModelModal()" color="primary">
                Pull Model
            </x-filament::button>
            <x-filament::button tag="button" icon="heroicon-o-arrow-path" wire:click="$parent.refreshOllamaData()" color="gray">
                Refresh
            </x-filament::button>
        </div>
    </div>

    @if (! empty($models))
        <div class="mt-4 overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-800">
                    <tr>
                        <th scope="col" class="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-200">Model Name</th>
                        <th scope="col" class="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-200">Size</th>
                        <th scope="col" class="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-200">Modified</th>
                        <th scope="col" class="px-4 py-3 text-left font-medium text-gray-700 dark:text-gray-200">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                    @foreach ($models as $model)
                        <tr class="bg-white dark:bg-gray-900/50">
                            <td class="px-4 py-3 text-gray-900 dark:text-gray-50">
                                {{ $model['name'] ?? 'Unknown' }}
                            </td>
                            <td class="px-4 py-3 text-gray-700 dark:text-gray-200">
                                {{ $model['size'] ?? '—' }}
                            </td>
                            <td class="px-4 py-3 text-gray-700 dark:text-gray-200">
                                {{ $model['modified'] ?? '—' }}
                            </td>
                            <td class="px-4 py-3">
                                <div class="flex items-center gap-2">
                                    <x-filament::button
                                        tag="button"
                                        color="danger"
                                        size="xs"
                                        wire:click.debounce="$parent.deleteModel('{{ $model['name'] ?? '' }}')"
                                        x-on:click.prevent="if(!confirm('Delete model {{ $model['name'] ?? '' }}?')) return false"
                                    >
                                        Delete
                                    </x-filament::button>
                                </div>
                            </td>
                        </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
    @else
        <div class="mt-6 rounded-lg border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-600 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
            No models available. Pull models via Ollama CLI or implement pull modal.
        </div>
    @endif
</div>

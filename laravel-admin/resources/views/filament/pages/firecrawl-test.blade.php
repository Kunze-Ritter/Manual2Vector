<x-filament-panels::page>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <x-filament::card>
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-semibold">Scraping Service Health</h2>
                    <p class="text-sm text-gray-500">Aggregated scraping backend health (Firecrawl + fallback)</p>
                </div>
                @if($health)
                    @php
                        $status = data_get($health, 'status', 'offline');
                        $statusColor = match ($status) {
                            'healthy' => 'success',
                            'degraded' => 'warning',
                            default => 'danger',
                        };
                    @endphp
                    <x-filament::badge color="{{ $statusColor }}">
                        {{ ucfirst($status) }}
                    </x-filament::badge>
                @else
                    <x-filament::badge color="danger">
                        Offline
                    </x-filament::badge>
                @endif
            </div>
            <div class="mt-4 space-y-2 text-sm text-gray-700">
                <div class="flex justify-between"><span>Backend</span><span>{{ $backendInfo['backend'] ?? 'firecrawl' }}</span></div>
                <div class="flex justify-between"><span>Capabilities</span><span>{{ implode(', ', $backendInfo['capabilities'] ?? []) }}</span></div>
                <div class="flex justify-between"><span>Fallbacks</span><span>{{ $backendInfo['fallback_count'] ?? 0 }}</span></div>
            </div>
        </x-filament::card>

        <x-filament::card>
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-semibold">Configuration</h2>
                    <p class="text-sm text-gray-500">Editable Firecrawl settings</p>
                </div>
                <x-filament::badge color="primary">Editable</x-filament::badge>
            </div>
            <div class="mt-4 space-y-4 text-sm text-gray-700">
                {{ $this->configForm }}
                <div class="flex justify-end gap-2">
                    <x-filament::button color="secondary" wire:click="reloadConfiguration" outlined>
                        Revert
                    </x-filament::button>
                    <x-filament::button color="primary" wire:click="saveConfiguration">
                        Update Config
                    </x-filament::button>
                </div>
            </div>
        </x-filament::card>

        <x-filament::card>
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-semibold">Test URLs</h2>
                    <p class="text-sm text-gray-500">Quick starts</p>
                </div>
            </div>
            <div class="mt-4 space-y-2 text-sm text-gray-700">
                @foreach(($configuration['test_urls'] ?? []) as $label => $url)
                    <div class="flex justify-between">
                        <span class="font-medium">{{ ucfirst($label) }}</span>
                        <span class="text-blue-600">{{ $url }}</span>
                    </div>
                @endforeach
            </div>
        </x-filament::card>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <x-filament::card>
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h2 class="text-lg font-semibold">Test Firecrawl Operations</h2>
                    <p class="text-sm text-gray-500">Scrape, crawl, extract, or map URLs</p>
                </div>
                @if($isLoading)
                    <x-filament::loading-indicator class="h-5 w-5 text-primary-600" />
                @endif
            </div>
            {{ $this->form }}
            <div class="mt-4 flex justify-end">
                <x-filament::button wire:click="runTest" :disabled="$isLoading">
                    Run Test
                </x-filament::button>
            </div>
        </x-filament::card>

        <x-filament::card>
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h2 class="text-lg font-semibold">Test Results</h2>
                    <p class="text-sm text-gray-500">Latest response payload</p>
                </div>
            </div>
            @if($testResult)
                <x-filament::section>
                    <pre class="text-xs bg-gray-900 text-gray-100 p-3 rounded overflow-x-auto">{{ json_encode($testResult, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) }}</pre>
                </x-filament::section>
            @else
                <p class="text-sm text-gray-500">No tests run yet.</p>
            @endif
        </x-filament::card>
    </div>

    <x-filament::card class="mt-6">
        <div class="flex items-center justify-between mb-4">
            <div>
                <h2 class="text-lg font-semibold">Recent Activity</h2>
                <p class="text-sm text-gray-500">Latest scraping events</p>
            </div>
        </div>
        @if(!empty($recentActivity['logs'] ?? []))
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                    <thead>
                        <tr>
                            <th class="px-3 py-2 text-left font-semibold">Timestamp</th>
                            <th class="px-3 py-2 text-left font-semibold">Action</th>
                            <th class="px-3 py-2 text-left font-semibold">URL</th>
                            <th class="px-3 py-2 text-left font-semibold">Backend</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
                        @foreach($recentActivity['logs'] as $log)
                            <tr>
                                <td class="px-3 py-2 whitespace-nowrap">{{ $log['timestamp'] ?? '-' }}</td>
                                <td class="px-3 py-2 whitespace-nowrap">{{ $log['action'] ?? '-' }}</td>
                                <td class="px-3 py-2 whitespace-nowrap text-blue-600">{{ $log['url'] ?? '-' }}</td>
                                <td class="px-3 py-2 whitespace-nowrap">{{ $log['backend'] ?? '-' }}</td>
                            </tr>
                        @endforeach
                    </tbody>
                </table>
            </div>
        @else
            <p class="text-sm text-gray-500">No recent activity available.</p>
        @endif
    </x-filament::card>
</x-filament-panels::page>

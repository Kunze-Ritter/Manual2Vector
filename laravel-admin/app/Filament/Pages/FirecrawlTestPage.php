<?php

namespace App\Filament\Pages;

use App\Services\FirecrawlService;
use Filament\Forms\Contracts\HasForms;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms;
use Filament\Schemas\Schema;
use Filament\Schemas\Components\Grid;
use Filament\Notifications\Notification;
use Filament\Pages\Page;

class FirecrawlTestPage extends Page implements HasForms
{
    use InteractsWithForms;

    protected static ?string $navigationLabel = 'Firecrawl Test';
    protected static \UnitEnum|string|null $navigationGroup = 'Services';
    protected static \BackedEnum|string|null $navigationIcon = 'heroicon-o-globe-alt';
    protected static ?int $navigationSort = 2;
    protected static ?string $pollingInterval = null;

    public array $formData = [
        'testType' => 'scrape',
        'testUrl' => '',
        'testOptions' => [],
        'testSchema' => [],
    ];
    public array $configData = [
        'provider' => null,
        'model_name' => null,
        'embedding_model' => null,
        'max_concurrency' => null,
        'block_media' => null,
    ];
    public ?array $health = null;
    public ?array $testResult = null;
    public ?bool $isLoading = false;
    public ?array $backendInfo = null;
    public ?array $configuration = null;
    public ?array $recentActivity = null;

    public function mount(): void
    {
        $service = app(FirecrawlService::class);
        $this->backendInfo = $service->getBackendInfo()['data'] ?? null;
        $this->health = $service->getHealth()['data'] ?? null;
        $this->configuration = $service->getConfiguration();
        $this->configData = [
            'provider' => $this->configuration['provider'] ?? $this->configuration['llm_provider'] ?? null,
            'model_name' => $this->configuration['model_name'] ?? null,
            'embedding_model' => $this->configuration['embedding_model'] ?? null,
            'max_concurrency' => $this->configuration['max_concurrency'] ?? null,
            'block_media' => $this->configuration['block_media'] ?? null,
        ];
        $this->recentActivity = $service->getRecentActivity()['data'] ?? null;
    }

    public function runTest(): void
    {
        $this->isLoading = true;
        $service = app(FirecrawlService::class);
        try {
            $options = is_array($this->formData['testOptions'] ?? null) ? $this->formData['testOptions'] : [];
            $schema = is_array($this->formData['testSchema'] ?? null) ? $this->formData['testSchema'] : [];
            $url = (string) ($this->formData['testUrl'] ?? '');
            $type = (string) ($this->formData['testType'] ?? 'scrape');

            $result = match ($type) {
                'crawl' => $service->crawlViaBackend($url, $options),
                'extract' => $service->extractViaBackend($url, $schema, $options),
                'map' => $service->mapViaBackend($url, $options),
                default => $service->scrapeViaBackend($url, $options),
            };

            $this->testResult = $result;

            Notification::make()
                ->title('Firecrawl test completed')
                ->success()
                ->send();
        } catch (\Throwable $e) {
            $this->testResult = [
                'success' => false,
                'error' => $e->getMessage(),
            ];

            Notification::make()
                ->title('Test failed')
                ->body($e->getMessage())
                ->danger()
                ->send();
        } finally {
            $this->isLoading = false;
        }
    }

    protected function decodeJson($state): array
    {
        if (is_array($state)) {
            return $state;
        }
        if (!is_string($state) || trim($state) === '') {
            return [];
        }
        try {
            $decoded = json_decode($state, true, 512, JSON_THROW_ON_ERROR);
            return is_array($decoded) ? $decoded : [];
        } catch (\Throwable) {
            return [];
        }
    }

    protected function encodeJson($state): string
    {
        if (empty($state)) {
            return '';
        }
        return json_encode($state, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    }

    protected function getForms(): array
    {
        return [
            'form' => Schema::make($this)
                ->components([
                    Forms\Components\Select::make('testType')
                        ->label('Test Type')
                        ->options([
                            'scrape' => 'Scrape URL',
                            'crawl' => 'Crawl Site',
                            'extract' => 'Extract Structured',
                            'map' => 'Map URLs',
                        ])
                        ->required()
                        ->reactive(),
                    Forms\Components\TextInput::make('testUrl')
                        ->label('URL')
                        ->placeholder('https://example.com')
                        ->required(),
                    Forms\Components\Textarea::make('testOptions')
                        ->label('Options (JSON)')
                        ->placeholder('{"blockMedia": true}')
                        ->rows(5)
                        ->dehydrateStateUsing(fn ($state) => $this->decodeJson($state))
                        ->afterStateHydrated(fn ($component, $state) => $component->state($this->encodeJson($state))),
                    Forms\Components\Textarea::make('testSchema')
                        ->label('Schema (JSON)')
                        ->placeholder('{"title": "string"}')
                        ->rows(6)
                        ->visible(fn (Forms\Get $get) => $get('testType') === 'extract')
                        ->dehydrateStateUsing(fn ($state) => $this->decodeJson($state))
                        ->afterStateHydrated(fn ($component, $state) => $component->state($this->encodeJson($state))),
                ])
                ->statePath('formData'),
            'configForm' => Schema::make($this)
                ->components([
                    Grid::make(2)->schema([
                        Forms\Components\TextInput::make('provider')
                            ->label('Provider')
                            ->required(),
                        Forms\Components\TextInput::make('model_name')
                            ->label('Model Name')
                            ->required(),
                        Forms\Components\TextInput::make('embedding_model')
                            ->label('Embedding Model'),
                        Forms\Components\TextInput::make('max_concurrency')
                            ->numeric()
                            ->minValue(1)
                            ->maxValue(10)
                            ->label('Max Concurrency'),
                        Forms\Components\Toggle::make('block_media')
                            ->label('Block Media'),
                    ]),
                ])
                ->statePath('configData'),
        ];
    }

    public function saveConfiguration(): void
    {
        $service = app(FirecrawlService::class);
        try {
            $validated = $this->validate([
                'configData.provider' => ['required', 'string'],
                'configData.model_name' => ['required', 'string'],
                'configData.embedding_model' => ['nullable', 'string'],
                'configData.max_concurrency' => ['nullable', 'integer', 'min:1', 'max:10'],
                'configData.block_media' => ['nullable', 'boolean'],
            ]);
            $result = $service->updateConfiguration($validated['configData']);
            if ($result['success'] ?? false) {
                Notification::make()
                    ->title('Configuration updated')
                    ->success()
                    ->send();
                $this->configuration = $result['data']['config'] ?? $validated['configData'];
                $this->configData = [
                    'provider' => $this->configuration['provider'] ?? $this->configuration['llm_provider'] ?? null,
                    'model_name' => $this->configuration['model_name'] ?? null,
                    'embedding_model' => $this->configuration['embedding_model'] ?? null,
                    'max_concurrency' => $this->configuration['max_concurrency'] ?? null,
                    'block_media' => $this->configuration['block_media'] ?? null,
                ];
                $this->health = $service->getHealth()['data'] ?? $this->health;
            } else {
                throw new \RuntimeException($result['error'] ?? 'Configuration update failed');
            }
        } catch (\Throwable $e) {
            Notification::make()
                ->title('Update failed')
                ->body($e->getMessage())
                ->danger()
                ->send();
        }
    }

    public function reloadConfiguration(): void
    {
        $service = app(FirecrawlService::class);
        $config = $service->getConfiguration();
        $this->configuration = $config;
        $this->configData = [
            'provider' => $config['provider'] ?? $config['llm_provider'] ?? null,
            'model_name' => $config['model_name'] ?? null,
            'embedding_model' => $config['embedding_model'] ?? null,
            'max_concurrency' => $config['max_concurrency'] ?? null,
            'block_media' => $config['block_media'] ?? null,
        ];
        $this->health = $service->getHealth()['data'] ?? $this->health;
    }
}

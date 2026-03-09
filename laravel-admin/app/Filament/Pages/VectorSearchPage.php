<?php

namespace App\Filament\Pages;

use Filament\Forms\Contracts\HasForms;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms;
use Filament\Notifications\Notification;
use Filament\Pages\Page;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Auth;

class VectorSearchPage extends Page implements HasForms
{
    use InteractsWithForms;

    protected string $view = 'filament.pages.vector-search';

    protected static ?string $navigationLabel = 'Semantic Search';
    protected static \UnitEnum|string|null $navigationGroup = 'Services';
    protected static \BackedEnum|string|null $navigationIcon = 'heroicon-o-magnifying-glass';
    protected static ?int $navigationSort = 3;
    protected static ?string $pollingInterval = null;

    public string $searchQuery = '';
    public int $limit = 10;
    public float $threshold = 0.5;
    public ?array $searchResults = null;
    public string|array|null $error = null;
    public bool $isSearching = false;
    public ?int $totalCount = null;
    public ?float $processingTime = null;

    public function search(): void
    {
        $this->validate([
            'searchQuery' => ['required', 'string', 'min:2'],
        ]);

        $this->isSearching = true;
        $this->error = null;
        $this->searchResults = null;

        try {
            $baseUrl = config('krai.engine_url');
            $timeout = config('krai.default_timeout', 120);

            $response = Http::timeout($timeout)
                ->withHeaders([
                    'Content-Type' => 'application/json',
                    'Accept' => 'application/json',
                ])
                ->withToken(config('krai.service_jwt'))
                ->post("{$baseUrl}/search", [
                    'query' => $this->searchQuery,
                    'limit' => $this->limit,
                    'offset' => 0,
                ]);

            if ($response->successful()) {
                $data = $response->json();
                $this->searchResults = $data['results'] ?? [];
                $this->totalCount = $data['total_count'] ?? count($this->searchResults);
                $this->processingTime = $data['processing_time_ms'] ?? null;

                Notification::make()
                    ->title('Suche abgeschlossen')
                    ->body("{$this->totalCount} Ergebnisse gefunden")
                    ->success()
                    ->send();
            } else {
                $this->error = $response->json('detail') ?? 'Search failed: HTTP ' . $response->status();
                
                Notification::make()
                    ->title('Suche fehlgeschlagen')
                    ->body($this->error)
                    ->danger()
                    ->send();
            }
        } catch (\Illuminate\Http\Client\ConnectionException $e) {
            $this->error = 'Verbindung zum Backend fehlgeschlagen. Bitte überprüfen Sie, ob der Engine-Dienst läuft.';
            
            Notification::make()
                ->title('Verbindungsfehler')
                ->body($this->error)
                ->danger()
                ->send();
        } catch (\Throwable $e) {
            $this->error = $e->getMessage();
            
            Notification::make()
                ->title('Fehler bei der Suche')
                ->body($this->error)
                ->danger()
                ->send();
        } finally {
            $this->isSearching = false;
        }
    }

    public function clearResults(): void
    {
        $this->searchQuery = '';
        $this->searchResults = null;
        $this->error = null;
        $this->totalCount = null;
        $this->processingTime = null;
    }

    protected function getSearchExamples(): array
    {
        return [
            'Drucker zeigt Fehlermeldung an',
            'Papierstau im hinteren Bereich',
            ' toner wechseln',
            'Netzwerkverbindung funktioniert nicht',
            'Farben werden nicht korrekt gedruckt',
        ];
    }

    public function searchExample(string $example): void
    {
        $this->searchQuery = $example;
        $this->search();
    }
}

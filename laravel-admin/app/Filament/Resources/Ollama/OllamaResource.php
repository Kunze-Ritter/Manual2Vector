<?php

namespace App\Filament\Resources\Ollama;

use App\Filament\Resources\Ollama\Pages\ManageOllama;
use Filament\Resources\Resource;
use Illuminate\Support\Facades\Http;

class OllamaResource extends Resource
{
    protected static ?string $model = null;

    public static function canViewAny(): bool
    {
        return auth()->user()->isAdmin();
    }

    public static function getNavigationLabel(): string
    {
        return 'Ollama Settings';
    }

    public static function getModelLabel(): string
    {
        return 'Ollama';
    }

    
    public static function getOllamaModels(): array
    {
        try {
            $response = Http::timeout(10)->get('http://krai-ollama-prod:11434/api/tags');
            
            if ($response->successful()) {
                return $response->json('models', []);
            }
        } catch (\Exception $e) {
            // Log error if needed
        }
        
        return [];
    }

    public static function getOllamaInfo(): array
    {
        try {
            $response = Http::timeout(10)->get('http://krai-ollama-prod:11434/api/version');
            
            if ($response->successful()) {
                return $response->json();
            }
        } catch (\Exception $e) {
            // Log error if needed
        }
        
        return [];
    }

    protected static function formatSize(string $size): string
    {
        $bytes = (int) $size;
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        
        for ($i = 0; $bytes > 1024 && $i < count($units) - 1; $i++) {
            $bytes /= 1024;
        }
        
        return round($bytes, 2) . ' ' . $units[$i];
    }
}

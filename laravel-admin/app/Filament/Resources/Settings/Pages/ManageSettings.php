<?php

namespace App\Filament\Resources\Settings\Pages;

use App\Filament\Resources\Settings\SettingsResource;
use App\Filament\Resources\Ollama\OllamaResource;
use Filament\Actions\Action;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\Page;
use Illuminate\Support\Facades\File;

class ManageSettings extends Page
{
    protected static string $resource = SettingsResource::class;

    protected string $view = 'filament.resources.settings.pages.manage-settings';

    public array $data = [];
    public array $models = [];
    public array $ollamaInfo = [];

    public function mount(): void
    {
        $this->data = $this->loadEnvValues();
        // Load Ollama data for AI Settings tab
        $this->loadOllamaData();
    }

    protected function getHeaderActions(): array
    {
        return [
            Action::make('save')
                ->label('Save Settings')
                ->action('save')
                ->icon('heroicon-o-check'),
        ];
    }

    public function save(): void
    {
        $envPath = env('KRAI_ROOT_ENV_PATH', base_path('.env'));

        if (! File::exists($envPath)) {
            Notification::make()
                ->title('Configuration Error')
                ->body('The target .env file does not exist.')
                ->danger()
                ->send();

            return;
        }

        $content = File::get($envPath);
        $lines = explode("\n", $content);
        $updatedLines = [];

        $allowedKeys = array_keys($this->data);

        foreach ($lines as $line) {
            $trimmed = trim($line);
            if ($trimmed === '' || str_starts_with($trimmed, '#')) {
                $updatedLines[] = $line;
                continue;
            }

            if (! str_contains($trimmed, '=')) {
                $updatedLines[] = $line;
                continue;
            }

            [$key] = explode('=', $trimmed, 2);
            $key = trim($key);

            if (in_array($key, $allowedKeys, true)) {
                $value = $this->data[$key];
                if (is_bool($value)) {
                    $value = $value ? 'true' : 'false';
                }
                $updatedLines[] = "{$key}={$value}";
            } else {
                $updatedLines[] = $line;
            }
        }

        File::put($envPath, implode("\n", $updatedLines));

        Notification::make()
            ->title('Settings Saved')
            ->body('The .env file has been updated. Restart services to apply changes.')
            ->success()
            ->send();
    }

    protected function loadOllamaData(): void
    {
        $this->models = OllamaResource::getOllamaModels();
        $this->ollamaInfo = OllamaResource::getOllamaInfo();
    }

    public function refreshOllamaData(): void
    {
        $this->loadOllamaData();
        Notification::make()
            ->title('Ollama Data Refreshed')
            ->body('Model list and status have been updated.')
            ->success()
            ->send();
    }

    public function deleteModel(string $modelName): void
    {
        try {
            $response = OllamaResource::deleteModel($modelName);
            
            if ($response['success'] ?? false) {
                Notification::make()
                    ->title('Model Deleted')
                    ->body("Model '{$modelName}' has been deleted successfully.")
                    ->success()
                    ->send();
                
                $this->refreshOllamaData();
            } else {
                throw new \Exception($response['error'] ?? 'Unknown error');
            }
        } catch (\Exception $e) {
            Notification::make()
                ->title('Delete Failed')
                ->body("Failed to delete model '{$modelName}': " . $e->getMessage())
                ->danger()
                ->send();
        }
    }

    public function showPullModelModal(): void
    {
        // For now, just show a notification. In a real implementation, 
        // this would open a modal to select and pull a model
        Notification::make()
            ->title('Pull Model')
            ->body('Model pull functionality will be implemented in the modal.')
            ->info()
            ->send();
    }

    protected function loadEnvValues(): array
    {
        $envPath = env('KRAI_ROOT_ENV_PATH', base_path('.env'));

        if (! File::exists($envPath)) {
            return [];
        }

        $content = File::get($envPath);
        $lines = explode("\n", $content);
        $values = [];

        $allowedKeys = [
            'AI_SERVICE_TYPE',
            'AI_SERVICE_URL',
            'OLLAMA_URL',
            'AI_PROVIDER',
            'OPENAI_API_KEY',
            'OLLAMA_GPU_MEMORY',
            'OLLAMA_GPU_LAYERS',
            'OLLAMA_NUM_GPU',
            'OLLAMA_MODEL_EMBEDDING',
            'OLLAMA_MODEL_EXTRACTION',
            'OLLAMA_MODEL_CHAT',
            'OLLAMA_MODEL_VISION',
            'OLLAMA_NUM_CTX',
            'ENABLE_PRODUCT_EXTRACTION',
            'ENABLE_PARTS_EXTRACTION',
            'ENABLE_ERROR_CODE_EXTRACTION',
            'ENABLE_IMAGE_EXTRACTION',
            'ENABLE_OCR',
            'ENABLE_VISION_AI',
            'ENABLE_EMBEDDINGS',
            'LLM_MAX_PAGES',
            'MAX_VISION_IMAGES',
            'DISABLE_VISION_PROCESSING',
            'ENABLE_SOLUTION_TRANSLATION',
            'SOLUTION_TRANSLATION_LANGUAGE',
        ];

        foreach ($lines as $line) {
            $trimmed = trim($line);
            if ($trimmed === '' || str_starts_with($trimmed, '#') || ! str_contains($trimmed, '=')) {
                continue;
            }

            [$key, $value] = explode('=', $trimmed, 2);
            $key = trim($key);
            $value = trim($value);

            if (in_array($key, $allowedKeys, true)) {
                if (in_array($value, ['true', 'false'], true)) {
                    $values[$key] = $value === 'true';
                } elseif (is_numeric($value)) {
                    $values[$key] = (int) $value;
                } else {
                    $values[$key] = $value;
                }
            }
        }

        return $values;
    }
}

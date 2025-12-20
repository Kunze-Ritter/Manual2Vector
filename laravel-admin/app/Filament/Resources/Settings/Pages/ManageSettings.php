<?php

namespace App\Filament\Resources\Settings\Pages;

use App\Filament\Resources\Ollama\OllamaResource;
use App\Filament\Resources\Settings\Schemas\SettingsFormSchema;
use App\Filament\Resources\Settings\SettingsResource;
use Filament\Actions\Action;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;
use Filament\Forms\Form;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\Page;
use Illuminate\Support\Facades\File;

class ManageSettings extends Page implements HasForms
{
    use InteractsWithForms;

    protected static string $resource = SettingsResource::class;

    protected static bool $shouldCheckUnsavedChangesBeforeLeaving = true;

    protected const ALLOWED_ENV_KEYS = [
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

    public array $data = [];
    public array $models = [];
    public array $ollamaInfo = [];

    public function mount(): void
    {
        $this->loadOllamaData();
        $this->form->fill($this->loadEnvValues());
    }

    public function form(Form $form): Form
    {
        return SettingsFormSchema::configure($form)->statePath('data');
    }

    protected function getHeaderActions(): array
    {
        return [
            Action::make('save')
                ->label('Save Settings')
                ->submit('save')
                ->icon('heroicon-o-check'),
        ];
    }

    public function getFormActions(): array
    {
        return [
            Action::make('save')
                ->label('Save Settings')
                ->submit('save')
                ->color('primary')
                ->icon('heroicon-o-check'),
        ];
    }

    public function save(): void
    {
        $state = $this->form->getState();

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

        $allowedKeys = array_keys($state);

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
                $value = $state[$key] ?? null;
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

        foreach ($lines as $line) {
            $trimmed = trim($line);
            if ($trimmed === '' || str_starts_with($trimmed, '#') || ! str_contains($trimmed, '=')) {
                continue;
            }

            [$key, $value] = explode('=', $trimmed, 2);
            $key = trim($key);
            $value = trim($value);

            if (in_array($key, self::ALLOWED_ENV_KEYS, true)) {
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

    public function getOllamaModelOptions(): array
    {
        if (empty($this->models)) {
            return [];
        }

        return collect($this->models)
            ->pluck('name', 'name')
            ->toArray();
    }
}

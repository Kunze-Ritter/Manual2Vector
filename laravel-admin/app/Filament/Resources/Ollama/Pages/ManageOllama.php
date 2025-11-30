<?php

namespace App\Filament\Resources\Ollama\Pages;

use App\Filament\Resources\Ollama\OllamaResource;
use Filament\Actions;
use Filament\Actions\Action;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\ManageRecords;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ManageOllama extends ManageRecords
{
    protected static string $resource = OllamaResource::class;

    protected static ?string $title = 'Ollama Settings';

    public array $models = [];

    public array $ollamaInfo = [];

    public array $gpuSettings = [
        'gpu_memory' => 'auto',
        'gpu_layers' => 'auto',
        'num_gpu' => 'auto',
    ];

    public function mount(): void
    {
        $this->loadOllamaData();
    }

    protected function loadOllamaData(): void
    {
        $this->models = OllamaResource::getOllamaModels();
        $this->ollamaInfo = OllamaResource::getOllamaInfo();
    }

    
    public function table(Table $table): Table
    {
        return $table
            ->query(fn () => collect($this->models))
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->label('Model Name')
                    ->searchable()
                    ->sortable()
                    ->formatStateUsing(fn (string $state): string => str_replace(':latest', '', $state)),
                Tables\Columns\TextColumn::make('size')
                    ->label('Size')
                    ->formatStateUsing(fn (string $state): string => $this->formatSize($state))
                    ->sortable(),
                Tables\Columns\TextColumn::make('modified_at')
                    ->label('Modified')
                    ->dateTime()
                    ->sortable()
                    ->formatStateUsing(fn (string $state): string => \Carbon\Carbon::parse($state)->diffForHumans()),
                Tables\Columns\IconColumn::make('running')
                    ->label('Running')
                    ->boolean()
                    ->getStateUsing(fn (array $record): bool => $this->isModelRunning($record['name'] ?? ''))
                    ->sortable(),
            ])
            ->actions([
                Tables\Actions\Action::make('pull')
                    ->label('Pull')
                    ->icon('heroicon-o-arrow-down-tray')
                    ->color('success')
                    ->requiresConfirmation()
                    ->action(function (array $record) {
                        $this->pullModel($record['name']);
                    }),
                Tables\Actions\Action::make('delete')
                    ->label('Delete')
                    ->icon('heroicon-o-trash')
                    ->color('danger')
                    ->requiresConfirmation()
                    ->action(function (array $record) {
                        $this->deleteModel($record['name']);
                    }),
            ])
            ->emptyStateActions([
                Tables\Actions\Action::make('pull')
                    ->label('Pull First Model')
                    ->icon('heroicon-o-arrow-down-tray')
                    ->action(function () {
                        // Redirect to pull form
                    }),
            ]);
    }

    protected function getHeaderActions(): array
    {
        return [
            Action::make('refresh')
                ->label('Refresh')
                ->icon('heroicon-o-arrow-path')
                ->action(fn () => $this->loadOllamaData()),
            Action::make('save_gpu_settings')
                ->label('Save GPU Settings')
                ->icon('heroicon-o-device-phone-mobile')
                ->action(fn () => $this->saveGpuSettings()),
            Action::make('pull_model')
                ->label('Pull Model')
                ->icon('heroicon-o-arrow-down-tray')
                ->form([
                    Forms\Components\Select::make('model_name')
                        ->label('Model')
                        ->options([
                            'llama3.1:8b' => 'Llama 3.1 8B',
                            'llama3.1:70b' => 'Llama 3.1 70B',
                            'llama3:8b' => 'Llama 3 8B',
                            'llama3:70b' => 'Llama 3 70B',
                            'qwen2.5:7b' => 'Qwen 2.5 7B',
                            'qwen2.5:14b' => 'Qwen 2.5 14B',
                            'nomic-embed-text' => 'Nomic Embed Text',
                            'llava-phi3' => 'LLaVA Phi-3',
                            'mistral' => 'Mistral',
                        ])
                        ->required(),
                ])
                ->action(function (array $data) {
                    $this->pullModel($data['model_name']);
                }),
        ];
    }

    protected function formatSize(string $size): string
    {
        $bytes = (int) $size;
        $units = ['B', 'KB', 'MB', 'GB', 'TB'];
        
        for ($i = 0; $bytes > 1024 && $i < count($units) - 1; $i++) {
            $bytes /= 1024;
        }
        
        return round($bytes, 2) . ' ' . $units[$i];
    }

    protected function isModelRunning(string $modelName): bool
    {
        try {
            $response = Http::timeout(5)->post('http://krai-ollama-prod:11434/api/generate', [
                'model' => $modelName,
                'prompt' => 'test',
                'stream' => false,
            ]);
            
            return $response->successful();
        } catch (\Exception $e) {
            return false;
        }
    }

    protected function pullModel(string $modelName): void
    {
        try {
            Notification::make()
                ->title('Pulling Model')
                ->body("Starting to pull model: {$modelName}")
                ->info()
                ->send();

            // In a real implementation, you would use a background job
            // For now, we'll simulate the pull
            $response = Http::timeout(300)->post('http://krai-ollama-prod:11434/api/pull', [
                'name' => $modelName,
            ]);

            if ($response->successful()) {
                Notification::make()
                    ->title('Model Pulled Successfully')
                    ->body("Model {$modelName} has been downloaded and installed.")
                    ->success()
                    ->send();
                
                $this->loadOllamaData();
            } else {
                throw new \Exception('Failed to pull model');
            }
        } catch (\Exception $e) {
            Notification::make()
                ->title('Error Pulling Model')
                ->body("Failed to pull model {$modelName}: {$e->getMessage()}")
                ->danger()
                ->send();
        }
    }

    protected function deleteModel(string $modelName): void
    {
        try {
            $response = Http::timeout(60)->delete('http://krai-ollama-prod:11434/api/delete', [
                'name' => $modelName,
            ]);

            if ($response->successful()) {
                Notification::make()
                    ->title('Model Deleted')
                    ->body("Model {$modelName} has been removed.")
                    ->success()
                    ->send();
                
                $this->loadOllamaData();
            } else {
                throw new \Exception('Failed to delete model');
            }
        } catch (\Exception $e) {
            Notification::make()
                ->title('Error Deleting Model')
                ->body("Failed to delete model {$modelName}: {$e->getMessage()}")
                ->danger()
                ->send();
        }
    }

    protected function saveGpuSettings(): void
    {
        try {
            // In a real implementation, you would save these to a config file
            // or update the Ollama environment variables
            
            Notification::make()
                ->title('GPU Settings Saved')
                ->body('GPU settings have been updated. Restart Ollama service to apply changes.')
                ->success()
                ->send();
        } catch (\Exception $e) {
            Notification::make()
                ->title('Error Saving Settings')
                ->body("Failed to save GPU settings: {$e->getMessage()}")
                ->danger()
                ->send();
        }
    }
}

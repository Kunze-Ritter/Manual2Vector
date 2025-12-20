<?php

namespace App\Filament\Resources\Settings\Schemas;

use Closure;
use Filament\Forms\Components\Section;
use Filament\Forms\Components\Select;
use Filament\Forms\Components\Tabs;
use Filament\Forms\Components\Tabs\Tab;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Toggle;
use Filament\Forms\Components\ViewField;
use Filament\Forms\Form;

class SettingsFormSchema
{
    public static function configure(Form $schema): Form
    {
        return $schema->schema([
            Tabs::make('settings_tabs')
                ->contained(false)
                ->persistTabInQueryString()
                ->tabs([
                    Tab::make('General Settings')
                        ->icon('heroicon-o-cog-6-tooth')
                        ->schema([
                            Section::make('AI Service')
                                ->icon('heroicon-o-cpu-chip')
                                ->description('Configure which AI service and models are used by the KR-AI Engine.')
                                ->columns(['md' => 2, 'xl' => 2])
                                ->schema([
                                    TextInput::make('AI_SERVICE_TYPE')
                                        ->label('AI Service Type')
                                        ->default('ollama')
                                        ->required()
                                        ->hint('Usually "ollama"')
                                        ->maxLength(100),
                                    TextInput::make('AI_SERVICE_URL')
                                        ->label('AI Service URL')
                                        ->required()
                                        ->url()
                                        ->placeholder('http://krai-ollama-prod:11434')
                                        ->hint('Internal URL for AI service abstraction'),
                                    TextInput::make('OLLAMA_URL')
                                        ->label('Ollama URL')
                                        ->url()
                                        ->placeholder('http://krai-ollama-prod:11434')
                                        ->hint('URL used by backend for Ollama')
                                        ->visible(fn (Closure $get) => $get('AI_PROVIDER') === 'ollama')
                                        ->columnSpanFull(),
                                ]),
                            Section::make('LLM Models')
                                ->icon('heroicon-o-brain')
                                ->description('Select which models to use for different tasks.')
                                ->columns(['md' => 2, 'xl' => 2])
                                ->schema([
                                    Select::make('OLLAMA_MODEL_EMBEDDING')
                                        ->label('Embedding Model')
                                        ->options(fn ($livewire) => $livewire->getOllamaModelOptions() + [
                                            'nomic-embed-text' => 'nomic-embed-text',
                                            'mxbai-embed-large' => 'mxbai-embed-large',
                                            'all-minilm' => 'all-minilm',
                                        ])
                                        ->searchable()
                                        ->hint('Model for vector generation'),
                                    Select::make('OLLAMA_MODEL_EXTRACTION')
                                        ->label('Extraction Model')
                                        ->options(fn ($livewire) => $livewire->getOllamaModelOptions() + [
                                            'llama3.1:8b' => 'llama3.1:8b',
                                            'llama3.1:70b' => 'llama3.1:70b',
                                            'llama3:8b' => 'llama3:8b',
                                            'llama3:70b' => 'llama3:70b',
                                            'qwen2.5:7b' => 'qwen2.5:7b',
                                            'qwen2.5:14b' => 'qwen2.5:14b',
                                        ])
                                        ->searchable()
                                        ->hint('Model for data extraction'),
                                    Select::make('OLLAMA_MODEL_CHAT')
                                        ->label('Chat Model')
                                        ->options(fn ($livewire) => $livewire->getOllamaModelOptions() + [
                                            'llama3.1:8b' => 'llama3.1:8b',
                                            'llama3.1:70b' => 'llama3.1:70b',
                                            'llama3:8b' => 'llama3:8b',
                                            'llama3:70b' => 'llama3:70b',
                                            'qwen2.5:7b' => 'qwen2.5:7b',
                                            'qwen2.5:14b' => 'qwen2.5:14b',
                                        ])
                                        ->searchable()
                                        ->hint('Model for chat responses'),
                                    Select::make('OLLAMA_MODEL_VISION')
                                        ->label('Vision Model')
                                        ->options(fn ($livewire) => $livewire->getOllamaModelOptions() + [
                                            'llava-phi3' => 'llava-phi3',
                                            'llava' => 'llava',
                                            'llava-llama3' => 'llava-llama3',
                                            'moondream' => 'moondream',
                                        ])
                                        ->searchable()
                                        ->hint('Model for image analysis'),
                                    TextInput::make('OLLAMA_NUM_CTX')
                                        ->label('Context Size')
                                        ->numeric()
                                        ->default(4096)
                                        ->minValue(512)
                                        ->maxValue(32768)
                                        ->hint('Maximum context window size'),
                                ]),
                            Section::make('Processing Flags')
                                ->icon('heroicon-o-flag')
                                ->description('Toggle features on/off for the processing pipeline.')
                                ->columns(['md' => 2, 'xl' => 2])
                                ->schema([
                                    Toggle::make('ENABLE_PRODUCT_EXTRACTION')
                                        ->label('Enable Product Extraction')
                                        ->helperText('Extract product information from documents'),
                                    Toggle::make('ENABLE_PARTS_EXTRACTION')
                                        ->label('Enable Parts Extraction')
                                        ->helperText('Extract parts information from documents'),
                                    Toggle::make('ENABLE_ERROR_CODE_EXTRACTION')
                                        ->label('Enable Error Code Extraction')
                                        ->helperText('Extract error codes and troubleshooting info'),
                                    Toggle::make('ENABLE_IMAGE_EXTRACTION')
                                        ->label('Enable Image Extraction')
                                        ->helperText('Extract images from documents'),
                                    Toggle::make('ENABLE_OCR')
                                        ->label('Enable OCR')
                                        ->helperText('Extract text from images using OCR'),
                                    Toggle::make('ENABLE_VISION_AI')
                                        ->label('Enable Vision AI')
                                        ->helperText('Analyze images with AI models'),
                                    Toggle::make('ENABLE_EMBEDDINGS')
                                        ->label('Enable Embeddings')
                                        ->helperText('Generate embeddings for semantic search'),
                                    TextInput::make('LLM_MAX_PAGES')
                                        ->label('LLM Max Pages')
                                        ->numeric()
                                        ->default(10)
                                        ->minValue(0)
                                        ->hint('Maximum pages to process per document'),
                                    TextInput::make('MAX_VISION_IMAGES')
                                        ->label('Max Vision Images')
                                        ->numeric()
                                        ->default(20)
                                        ->minValue(0)
                                        ->hint('Maximum images to analyze with Vision AI'),
                                    Toggle::make('DISABLE_VISION_PROCESSING')
                                        ->label('Disable Vision Processing')
                                        ->helperText('Completely disable vision/AI image processing'),
                                    Toggle::make('ENABLE_SOLUTION_TRANSLATION')
                                        ->label('Enable Solution Translation')
                                        ->helperText('Translate solutions to target language'),
                                    TextInput::make('SOLUTION_TRANSLATION_LANGUAGE')
                                        ->label('Translation Language')
                                        ->placeholder('de')
                                        ->maxLength(5)
                                        ->hint('Target language for translation (ISO code)')
                                        ->rules(['regex:/^[a-z]{2,5}$/'])
                                        ->columnSpanFull(),
                                ]),
                        ]),
                    Tab::make('AI Settings')
                        ->icon('heroicon-o-sparkles')
                        ->schema([
                            Section::make('AI Provider')
                                ->icon('heroicon-o-rocket-launch')
                                ->description('Choose between local Ollama or cloud-based OpenAI services.')
                                ->columns(['md' => 2, 'xl' => 2])
                                ->schema([
                                    Select::make('AI_PROVIDER')
                                        ->label('AI Provider')
                                        ->options([
                                            'ollama' => 'Ollama (Local)',
                                            'openai' => 'OpenAI (Cloud)',
                                        ])
                                        ->required()
                                        ->reactive()
                                        ->hint('Select your AI service provider'),
                                    TextInput::make('OPENAI_API_KEY')
                                        ->label('OpenAI API Key')
                                        ->password()
                                        ->placeholder('sk-...')
                                        ->visible(fn (Closure $get) => $get('AI_PROVIDER') === 'openai')
                                        ->columnSpanFull(),
                                ]),
                            Section::make('Ollama Management')
                                ->icon('heroicon-o-server-stack')
                                ->description('Manage local Ollama models and GPU settings.')
                                ->visible(fn (Closure $get) => $get('AI_PROVIDER') === 'ollama')
                                ->columns(['md' => 1, 'xl' => 1])
                                ->schema([
                                    ViewField::make('ollama_status')
                                        ->label('')
                                        ->view('filament.forms.components.ollama-status-display')
                                        ->state(fn ($livewire) => $livewire->ollamaInfo ?? [])
                                        ->columnSpanFull(),
                                    ViewField::make('ollama_models_table')
                                        ->label('')
                                        ->view('filament.forms.components.ollama-models-table')
                                        ->state(fn ($livewire) => $livewire->models ?? [])
                                        ->columnSpanFull(),
                                ]),
                            Section::make('GPU Settings')
                                ->icon('heroicon-o-adjustments-horizontal')
                                ->description('Configure GPU acceleration for Ollama models.')
                                ->visible(fn (Closure $get) => $get('AI_PROVIDER') === 'ollama')
                                ->columns(['md' => 3, 'xl' => 3])
                                ->schema([
                                    TextInput::make('OLLAMA_GPU_MEMORY')
                                        ->label('GPU Memory')
                                        ->placeholder('auto')
                                        ->hint('GPU memory allocation (e.g., 8192, auto)'),
                                    TextInput::make('OLLAMA_GPU_LAYERS')
                                        ->label('GPU Layers')
                                        ->placeholder('auto')
                                        ->hint('Number of GPU layers (e.g., 999, auto)'),
                                    TextInput::make('OLLAMA_NUM_GPU')
                                        ->label('Number of GPUs')
                                        ->placeholder('auto')
                                        ->hint('GPU count (e.g., 1, 2, auto)'),
                                ]),
                        ]),
                ]),
        ]);
    }
}

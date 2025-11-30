<x-filament-panels::page>
    <form wire:submit="save">
        <div class="space-y-8">
            <!-- Tab Navigation -->
            <div x-data="{ activeTab: 'general' }" class="border-b border-gray-200">
                <nav class="-mb-px flex space-x-8">
                    <button type="button" 
                            @click="activeTab = 'general'"
                            :class="activeTab === 'general' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                            class="whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors">
                        General Settings
                    </button>
                    <button type="button"
                            @click="activeTab = 'ai'"
                            :class="activeTab === 'ai' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                            class="whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors">
                        AI Settings
                    </button>
                </nav>

                <!-- Tab Content -->
                <!-- General Settings Tab -->
                <div x-show="activeTab === 'general'" x-transition:enter="transition ease-out duration-100" x-transition:enter-start="opacity-0" x-transition:enter-end="opacity-100">
                    <div class="space-y-8">
            <!-- AI Service Section -->
            <x-filament::section>
                <x-slot name="heading">
                    <div class="flex items-center gap-2">
                        <x-filament::icon icon="heroicon-o-cog-6-tooth" class="h-5 w-5 text-gray-600" />
                        <span class="text-lg font-semibold text-gray-900">AI Service</span>
                    </div>
                </x-slot>
                <x-slot name="description">
                    <p class="text-sm text-gray-600">Configure which AI service and models are used by the KR-AI Engine.</p>
                </x-slot>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <x-filament::input
                        label="AI Service Type"
                        wire:model="data.AI_SERVICE_TYPE"
                        placeholder="ollama"
                        hint="Usually 'ollama'"
                        required
                    />
                    
                    <x-filament::input
                        label="AI Service URL"
                        wire:model="data.AI_SERVICE_URL"
                        placeholder="http://krai-ollama-prod:11434"
                        hint="Internal URL for AI service abstraction"
                        required
                    />
                    
                    <x-filament::input
                        label="Ollama URL"
                        wire:model="data.OLLAMA_URL"
                        placeholder="http://krai-ollama-prod:11434"
                        hint="URL used by backend for Ollama"
                        x-show="data.AI_PROVIDER === 'ollama'"
                        class="md:col-span-2"
                    />
                </div>
            </x-filament::section>

            <!-- LLM Models Section -->
            <x-filament::section>
                <x-slot name="heading">
                    <div class="flex items-center gap-2">
                        <x-filament::icon icon="heroicon-o-cpu-chip" class="h-5 w-5 text-gray-600" />
                        <span class="text-lg font-semibold text-gray-900">LLM Models</span>
                    </div>
                </x-slot>
                <x-slot name="description">
                    <p class="text-sm text-gray-600">Select which models to use for different tasks.</p>
                </x-slot>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <x-filament::select
                        label="Embedding Model"
                        wire:model="data.OLLAMA_MODEL_EMBEDDING"
                        placeholder="Select model..."
                        hint="Model for vector generation"
                    >
                        <option value="">Select model...</option>
                        <option value="nomic-embed-text">nomic-embed-text</option>
                        <option value="mxbai-embed-large">mxbai-embed-large</option>
                        <option value="all-minilm">all-minilm</option>
                    </x-filament::select>
                    
                    <x-filament::select
                        label="Extraction Model"
                        wire:model="data.OLLAMA_MODEL_EXTRACTION"
                        placeholder="Select model..."
                        hint="Model for data extraction"
                    >
                        <option value="">Select model...</option>
                        <option value="llama3.1:8b">llama3.1:8b</option>
                        <option value="llama3.1:70b">llama3.1:70b</option>
                        <option value="llama3:8b">llama3:8b</option>
                        <option value="llama3:70b">llama3:70b</option>
                        <option value="qwen2.5:7b">qwen2.5:7b</option>
                        <option value="qwen2.5:14b">qwen2.5:14b</option>
                    </x-filament::select>
                    
                    <x-filament::select
                        label="Chat Model"
                        wire:model="data.OLLAMA_MODEL_CHAT"
                        placeholder="Select model..."
                        hint="Model for chat responses"
                    >
                        <option value="">Select model...</option>
                        <option value="llama3.1:8b">llama3.1:8b</option>
                        <option value="llama3.1:70b">llama3.1:70b</option>
                        <option value="llama3:8b">llama3:8b</option>
                        <option value="llama3:70b">llama3:70b</option>
                        <option value="qwen2.5:7b">qwen2.5:7b</option>
                        <option value="qwen2.5:14b">qwen2.5:14b</option>
                    </x-filament::select>
                    
                    <x-filament::select
                        label="Vision Model"
                        wire:model="data.OLLAMA_MODEL_VISION"
                        placeholder="Select model..."
                        hint="Model for image analysis"
                    >
                        <option value="">Select model...</option>
                        <option value="llava-phi3">llava-phi3</option>
                        <option value="llava">llava</option>
                        <option value="llava-llama3">llava-llama3</option>
                        <option value="moondream">moondream</option>
                    </x-filament::select>
                    
                    <x-filament::input
                        label="Context Size"
                        wire:model="data.OLLAMA_NUM_CTX"
                        type="number"
                        placeholder="4096"
                        hint="Maximum context window size"
                    />
                </div>
            </x-filament::section>

            <!-- Processing Flags Section -->
            <x-filament::section>
                <x-slot name="heading">
                    <div class="flex items-center gap-2">
                        <x-filament::icon icon="heroicon-o-flag" class="h-5 w-5 text-gray-600" />
                        <span class="text-lg font-semibold text-gray-900">Processing Flags</span>
                    </div>
                </x-slot>
                <x-slot name="description">
                    <p class="text-sm text-gray-600">Toggle features on/off for the processing pipeline.</p>
                </x-slot>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.ENABLE_PRODUCT_EXTRACTION"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Enable Product Extraction</span>
                            <span class="block text-xs text-gray-500">Extract product information from documents</span>
                        </span>
                    </label>

                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.ENABLE_PARTS_EXTRACTION"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Enable Parts Extraction</span>
                            <span class="block text-xs text-gray-500">Extract parts information from documents</span>
                        </span>
                    </label>

                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.ENABLE_ERROR_CODE_EXTRACTION"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Enable Error Code Extraction</span>
                            <span class="block text-xs text-gray-500">Extract error codes and troubleshooting info</span>
                        </span>
                    </label>

                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.ENABLE_IMAGE_EXTRACTION"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Enable Image Extraction</span>
                            <span class="block text-xs text-gray-500">Extract images from documents</span>
                        </span>
                    </label>

                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.ENABLE_OCR"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Enable OCR</span>
                            <span class="block text-xs text-gray-500">Extract text from images using OCR</span>
                        </span>
                    </label>

                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.ENABLE_VISION_AI"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Enable Vision AI</span>
                            <span class="block text-xs text-gray-500">Analyze images with AI models</span>
                        </span>
                    </label>

                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.ENABLE_EMBEDDINGS"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Enable Embeddings</span>
                            <span class="block text-xs text-gray-500">Generate embeddings for semantic search</span>
                        </span>
                    </label>
                    
                    <x-filament::input
                        label="LLM Max Pages"
                        wire:model="data.LLM_MAX_PAGES"
                        type="number"
                        placeholder="10"
                        hint="Maximum pages to process per document"
                    />
                    
                    <x-filament::input
                        label="Max Vision Images"
                        wire:model="data.MAX_VISION_IMAGES"
                        type="number"
                        placeholder="20"
                        hint="Maximum images to analyze with Vision AI"
                    />
                    
                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.DISABLE_VISION_PROCESSING"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Disable Vision Processing</span>
                            <span class="block text-xs text-gray-500">Completely disable vision/AI image processing</span>
                        </span>
                    </label>

                    <label class="flex items-start gap-2">
                        <input
                            type="checkbox"
                            wire:model="data.ENABLE_SOLUTION_TRANSLATION"
                            class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>
                            <span class="block text-sm font-medium text-gray-900">Enable Solution Translation</span>
                            <span class="block text-xs text-gray-500">Translate solutions to target language</span>
                        </span>
                    </label>
                    
                    <x-filament::input
                        label="Solution Translation Language"
                        wire:model="data.SOLUTION_TRANSLATION_LANGUAGE"
                        placeholder="de"
                        hint="Target language for translation (ISO code)"
                        class="md:col-span-2"
                    />
                </div>
            </x-filament::section>
                    </div>
                </div>

                <!-- AI Settings Tab -->
                <div x-show="activeTab === 'ai'" x-transition:enter="transition ease-out duration-100" x-transition:enter-start="opacity-0" x-transition:enter-end="opacity-100">
                    <div class="space-y-8">
                    <!-- AI Provider Selection -->
                    <x-filament::section>
                        <x-slot name="heading">
                            <div class="flex items-center gap-2">
                                <x-filament::icon icon="heroicon-o-cpu-chip" class="h-5 w-5 text-gray-600" />
                                <span class="text-lg font-semibold text-gray-900">AI Provider</span>
                            </div>
                        </x-slot>
                        <x-slot name="description">
                            <p class="text-sm text-gray-600">Choose between local Ollama or cloud-based OpenAI services.</p>
                        </x-slot>
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <x-filament::select
                                label="AI Provider"
                                wire:model="data.AI_PROVIDER"
                                hint="Select your AI service provider"
                            >
                                <option value="ollama">Ollama (Local)</option>
                                <option value="openai">OpenAI (Cloud)</option>
                            </x-filament::select>
                            
                            <x-filament::input
                                label="OpenAI API Key"
                                wire:model="data.OPENAI_API_KEY"
                                type="password"
                                placeholder="sk-..."
                                hint="Your OpenAI API key (BYOK - Bring Your Own Key)"
                                x-show="data.AI_PROVIDER === 'openai'"
                            />
                        </div>
                    </x-filament::section>

                    <!-- Ollama Management -->
                    <x-filament::section x-show="data.AI_PROVIDER === 'ollama'">
                        <x-slot name="heading">
                            <div class="flex items-center gap-2">
                                <x-filament::icon icon="heroicon-o-server-stack" class="h-5 w-5 text-gray-600" />
                                <span class="text-lg font-semibold text-gray-900">Ollama Management</span>
                            </div>
                        </x-slot>
                        <x-slot name="description">
                            <p class="text-sm text-gray-600">Manage local Ollama models and GPU settings.</p>
                        </x-slot>
                        
                        <div class="space-y-4">
                            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h4 class="font-medium text-blue-900 mb-2">Ollama Status</h4>
                                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                    <div>
                                        <span class="text-gray-600">Version:</span>
                                        <span class="ml-2 font-medium">{{ $ollamaInfo['version'] ?? 'Unknown' }}</span>
                                    </div>
                                    <div>
                                        <span class="text-gray-600">Build:</span>
                                        <span class="ml-2 font-medium">{{ $ollamaInfo['build'] ?? 'Unknown' }}</span>
                                    </div>
                                    <div>
                                        <span class="text-gray-600">Status:</span>
                                        <span class="ml-2 font-medium text-green-600">{{ $ollamaInfo['status'] ?? 'Unknown' }}</span>
                                    </div>
                                    <div>
                                        <span class="text-gray-600">Models:</span>
                                        <span class="ml-2 font-medium">{{ count($models) ?? 0 }}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="flex gap-2">
                                <button type="button" wire:click="loadOllamaData" 
                                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                                    Refresh Ollama Data
                                </button>
                                <button type="button" wire:click="showPullModelModal" 
                                        class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                                    Pull New Model
                                </button>
                            </div>
                            
                            <!-- Models Table (simplified version) -->
                            @if(!empty($models))
                            <div class="overflow-x-auto">
                                <table class="min-w-full divide-y divide-gray-200">
                                    <thead class="bg-gray-50">
                                        <tr>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Modified</th>
                                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody class="bg-white divide-y divide-gray-200">
                                        @foreach($models as $model)
                                        <tr>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {{ $model['name'] ?? 'Unknown' }}
                                            </td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {{ $model['size'] ?? 'Unknown' }}
                                            </td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {{ $model['modified_at'] ?? 'Unknown' }}
                                            </td>
                                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                <button type="button" wire:click="deleteModel('{{ $model['name'] }}')" 
                                                        class="text-red-600 hover:text-red-900">
                                                    Delete
                                                </button>
                                            </td>
                                        </tr>
                                        @endforeach
                                    </tbody>
                                </table>
                            </div>
                            @else
                            <div class="text-center py-8 text-gray-500">
                                <p>No Ollama models found. Click "Pull New Model" to get started.</p>
                            </div>
                            @endif
                        </div>
                    </x-filament::section>

                    <!-- GPU Settings -->
                    <x-filament::section x-show="data.AI_PROVIDER === 'ollama'">
                        <x-slot name="heading">
                            <div class="flex items-center gap-2">
                                <x-filament::icon icon="heroicon-o-cpu-chip" class="h-5 w-5 text-gray-600" />
                                <span class="text-lg font-semibold text-gray-900">GPU Settings</span>
                            </div>
                        </x-slot>
                        <x-slot name="description">
                            <p class="text-sm text-gray-600">Configure GPU acceleration for Ollama models.</p>
                        </x-slot>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <x-filament::input
                                label="GPU Memory"
                                wire:model="data.OLLAMA_GPU_MEMORY"
                                placeholder="auto"
                                hint="GPU memory allocation (e.g., 8192, auto)"
                            />
                            
                            <x-filament::input
                                label="GPU Layers"
                                wire:model="data.OLLAMA_GPU_LAYERS"
                                placeholder="auto"
                                hint="Number of GPU layers (e.g., 999, auto)"
                            />
                            
                            <x-filament::input
                                label="Number of GPUs"
                                wire:model="data.OLLAMA_NUM_GPU"
                                placeholder="auto"
                                hint="GPU count (e.g., 1, 2, auto)"
                            />
                        </div>
                    </x-filament::section>
                    </div>
                </div>
            </div>
        </div>
    </form>
</x-filament-panels::page>

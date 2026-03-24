<?php

namespace Tests\Feature;

use App\Filament\Resources\Settings\Pages\ManageSettings;
use Illuminate\Support\Facades\Http;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class ManageSettingsTest extends TestCase
{
    protected string $ollamaUrl = 'http://krai-ollama-prod:11434';

    #[Test]
    public function settings_form_schema_uses_filament_schema_layout_components(): void
    {
        $schemaFile = file_get_contents(app_path('Filament/Resources/Settings/Schemas/SettingsFormSchema.php'));
        $pageFile = file_get_contents(app_path('Filament/Resources/Settings/Pages/ManageSettings.php'));

        $this->assertIsString($schemaFile);
        $this->assertIsString($pageFile);
        $this->assertStringContainsString('use Filament\\Schemas\\Components\\Section;', $schemaFile);
        $this->assertStringContainsString('use Filament\\Schemas\\Components\\Tabs;', $schemaFile);
        $this->assertStringContainsString('use Filament\\Schemas\\Components\\Tabs\\Tab;', $schemaFile);
        $this->assertStringNotContainsString('use Filament\\Forms\\Components\\Tabs;', $schemaFile);
        $this->assertStringContainsString("->view('filament.forms.components.ollama-status-display')", $schemaFile);
        $this->assertStringContainsString("->view('filament.forms.components.ollama-models-table')", $schemaFile);
        $this->assertStringNotContainsString('->state(fn ($livewire) => $livewire->ollamaInfo ?? [])', $schemaFile);
        $this->assertStringNotContainsString('->state(fn ($livewire) => $livewire->models ?? [])', $schemaFile);
        $this->assertStringContainsString('public function content(Schema $schema): Schema', $pageFile);
        $this->assertStringContainsString('$this->getFormContentComponent()', $pageFile);
        $this->assertStringContainsString("return Form::make([EmbeddedSchema::make('form')])", $pageFile);
        $this->assertStringContainsString('Actions::make($this->getFormActions())', $pageFile);
        $this->assertStringNotContainsString("protected string \$view = 'filament.resources.settings.pages.manage-settings';", $pageFile);

        $statusView = file_get_contents(resource_path('views/filament/forms/components/ollama-status-display.blade.php'));
        $modelsView = file_get_contents(resource_path('views/filament/forms/components/ollama-models-table.blade.php'));

        $this->assertIsString($statusView);
        $this->assertIsString($modelsView);
        $this->assertStringContainsString('$this->ollamaInfo ?? []', $statusView);
        $this->assertStringContainsString('$this->models ?? []', $modelsView);
    }

    #[Test]
    public function load_ollama_helpers_return_model_and_status_data_without_missing_resource_class(): void
    {
        Http::fake([
            "{$this->ollamaUrl}/api/tags" => Http::response([
                'models' => [
                    [
                        'name' => 'llama3.1:8b',
                        'size' => 1073741824,
                        'modified_at' => '2026-03-23T10:00:00Z',
                    ],
                ],
            ], 200),
            "{$this->ollamaUrl}/api/version" => Http::response([
                'version' => '0.7.0',
                'build' => 'abc123',
            ], 200),
        ]);

        $page = new class extends ManageSettings
        {
            public function exposedLoadOllamaData(): void
            {
                $this->loadOllamaData();
            }
        };

        $page->exposedLoadOllamaData();

        $this->assertSame('llama3.1:8b', $page->models[0]['name']);
        $this->assertSame('1.0 GB', $page->models[0]['size']);
        $this->assertSame('online', $page->ollamaInfo['status']);
        $this->assertSame('0.7.0', $page->ollamaInfo['version']);
        $this->assertSame(1, $page->ollamaInfo['model_count']);
    }

    #[Test]
    public function delete_model_uses_ollama_delete_endpoint(): void
    {
        Http::fake([
            "{$this->ollamaUrl}/api/delete" => Http::response([], 200),
            "{$this->ollamaUrl}/api/tags" => Http::response(['models' => []], 200),
            "{$this->ollamaUrl}/api/version" => Http::response(['version' => '0.7.0'], 200),
        ]);

        $page = new class extends ManageSettings
        {
            public function exposedDeleteModel(string $modelName): void
            {
                $this->deleteModel($modelName);
            }
        };

        $page->exposedDeleteModel('llama3.1:8b');

        Http::assertSent(function ($request): bool {
            return $request->method() === 'POST'
                && $request->url() === "{$this->ollamaUrl}/api/delete"
                && $request['name'] === 'llama3.1:8b';
        });
    }
}

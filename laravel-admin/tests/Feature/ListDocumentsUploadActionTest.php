<?php

namespace Tests\Feature;

use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class ListDocumentsUploadActionTest extends TestCase
{
    #[Test]
    public function upload_action_keeps_livewire_temp_file_and_exposes_optional_product_context_fields(): void
    {
        $source = file_get_contents(app_path('Filament/Resources/Documents/Pages/ListDocuments.php'));

        $this->assertIsString($source);
        $this->assertStringContainsString("->storeFiles(false)", $source);
        $this->assertStringContainsString("Select::make('manufacturer')", $source);
        $this->assertStringContainsString("Select::make('series')", $source);
        $this->assertStringContainsString("Select::make('model')", $source);
        $this->assertStringContainsString("Leer lassen für Auto-Erkennung", $source);
    }
}

<?php

namespace Tests\Feature;

use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class DocumentFormSchemaTest extends TestCase
{
    #[Test]
    public function document_form_uses_explicit_manufacturer_options_instead_of_relationship_binding(): void
    {
        $source = file_get_contents(app_path('Filament/Resources/Documents/Schemas/DocumentForm.php'));

        $this->assertIsString($source);
        $this->assertStringContainsString("Select::make('manufacturer_id')", $source);
        $this->assertStringContainsString("Manufacturer::query()", $source);
        $this->assertStringNotContainsString("->relationship('manufacturer', 'name')", $source);
    }
}

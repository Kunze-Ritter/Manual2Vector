<?php

namespace Tests\Feature;

use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class DocumentStageSelectionTest extends TestCase
{
    #[Test]
    public function manual_document_stage_actions_exclude_upload_stage(): void
    {
        $editSource = file_get_contents(app_path('Filament/Resources/Documents/Pages/EditDocument.php'));
        $tableSource = file_get_contents(app_path('Filament/Resources/Documents/Tables/DocumentsTable.php'));

        $this->assertIsString($editSource);
        $this->assertIsString($tableSource);
        $this->assertStringContainsString("->except(['upload'])", $editSource);
        $this->assertStringContainsString("->except(['upload'])", $tableSource);
    }
}

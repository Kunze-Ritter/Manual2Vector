<?php

namespace Tests\Feature;

use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class PipelineErrorResourceTest extends TestCase
{
    #[Test]
    public function pipeline_error_resource_eager_loads_real_user_name_columns(): void
    {
        $source = file_get_contents(app_path('Filament/Resources/Monitoring/PipelineErrorResource.php'));

        $this->assertIsString($source);
        $this->assertStringContainsString("resolvedBy:id,first_name,last_name,username,email", $source);
        $this->assertStringNotContainsString("resolvedBy:id,name", $source);
    }
}

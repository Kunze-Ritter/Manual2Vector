<?php

namespace Tests\Unit;

use App\Enums\DocumentProcessingStatus;
use App\Enums\UserRole;
use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class DocumentProcessingStatusTest extends TestCase
{
    #[Test]
    public function label_for_accepts_enum_instances_and_raw_strings(): void
    {
        $this->assertSame('Uploaded', DocumentProcessingStatus::labelFor(DocumentProcessingStatus::Uploaded));
        $this->assertSame('Completed', DocumentProcessingStatus::labelFor('completed'));
        $this->assertSame('unexpected', DocumentProcessingStatus::labelFor('unexpected'));
        $this->assertSame('', DocumentProcessingStatus::labelFor(null));
    }

    #[Test]
    public function user_role_label_for_accepts_enum_instances_and_raw_strings(): void
    {
        $this->assertSame('Admin', UserRole::labelFor(UserRole::Admin));
        $this->assertSame('Editor', UserRole::labelFor('editor'));
        $this->assertSame('unexpected', UserRole::labelFor('unexpected'));
        $this->assertSame('', UserRole::labelFor(null));
    }
}

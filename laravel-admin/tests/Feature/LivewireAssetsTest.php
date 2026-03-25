<?php

namespace Tests\Feature;

use PHPUnit\Framework\Attributes\Test;
use Tests\TestCase;

class LivewireAssetsTest extends TestCase
{
    #[Test]
    public function published_livewire_asset_matches_the_installed_package_asset(): void
    {
        $publishedAsset = public_path('vendor/livewire/livewire.js');
        $packageAsset = base_path('vendor/livewire/livewire/dist/livewire.js');

        $this->assertFileExists($publishedAsset);
        $this->assertFileExists($packageAsset);
        $this->assertSame(
            hash_file('sha256', $packageAsset),
            hash_file('sha256', $publishedAsset),
            'Published Livewire assets are stale. Re-sync them with `php scripts/sync_livewire_assets.php`.',
        );
    }
}

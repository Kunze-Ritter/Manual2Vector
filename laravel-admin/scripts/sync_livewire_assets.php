#!/usr/bin/env php
<?php

declare(strict_types=1);

$projectRoot = dirname(__DIR__);
$sourceDir = $projectRoot.DIRECTORY_SEPARATOR.'vendor'.DIRECTORY_SEPARATOR.'livewire'.DIRECTORY_SEPARATOR.'livewire'.DIRECTORY_SEPARATOR.'dist';
$targetDir = $projectRoot.DIRECTORY_SEPARATOR.'public'.DIRECTORY_SEPARATOR.'vendor'.DIRECTORY_SEPARATOR.'livewire';

if (! is_dir($sourceDir)) {
    fwrite(STDERR, "Livewire dist directory not found: {$sourceDir}".PHP_EOL);
    exit(1);
}

if (! is_dir($targetDir) && ! mkdir($targetDir, 0777, true) && ! is_dir($targetDir)) {
    fwrite(STDERR, "Could not create target directory: {$targetDir}".PHP_EOL);
    exit(1);
}

$sourceFiles = [];

foreach (glob($sourceDir.DIRECTORY_SEPARATOR.'*') ?: [] as $sourcePath) {
    if (! is_file($sourcePath)) {
        continue;
    }

    $filename = basename($sourcePath);
    $sourceFiles[$filename] = true;

    if (! copy($sourcePath, $targetDir.DIRECTORY_SEPARATOR.$filename)) {
        fwrite(STDERR, "Failed to copy {$filename}".PHP_EOL);
        exit(1);
    }
}

foreach (glob($targetDir.DIRECTORY_SEPARATOR.'*') ?: [] as $targetPath) {
    if (! is_file($targetPath)) {
        continue;
    }

    $filename = basename($targetPath);

    if (isset($sourceFiles[$filename])) {
        continue;
    }

    if (! unlink($targetPath)) {
        fwrite(STDERR, "Failed to remove stale file {$filename}".PHP_EOL);
        exit(1);
    }
}

ksort($sourceFiles);

echo 'Synced Livewire assets: '.implode(', ', array_keys($sourceFiles)).PHP_EOL;

<?php
require __DIR__ . '/laravel-admin/vendor/autoload.php';
$app = require_once __DIR__ . '/laravel-admin/bootstrap/app.php';
$app->boot();

try {
    echo "Testing bad route: ";
    echo route('filament.kradmin.resources.documents.documents.edit', 1);
    echo "\n";
} catch (Exception $e) {
    echo "ERROR: " . $e->getMessage() . "\n";
}

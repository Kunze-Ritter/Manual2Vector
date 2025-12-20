<?php

namespace App\Services;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ImageService
{
    private string $baseUrl;

    private string $serviceJwt;

    private int $cacheTtl;

    private int $statsCacheTtl;

    public function __construct(?string $baseUrl = null, ?string $serviceJwt = null, ?int $cacheTtl = null, ?int $statsCacheTtl = null)
    {
        $config = config('krai');
        $this->baseUrl = rtrim($baseUrl ?? ($config['engine_url'] ?? ''), '/');
        $this->serviceJwt = $serviceJwt ?? ($config['service_jwt'] ?? '');
        $imagesTtl = config('krai.images.cache_ttl', 60);
        $this->cacheTtl = $cacheTtl ?? $imagesTtl;
        $this->statsCacheTtl = $statsCacheTtl ?? 120;
    }

    private function client()
    {
        return Http::timeout(30)->withHeaders([
            'Authorization' => 'Bearer ' . $this->serviceJwt,
            'Accept' => 'application/json',
        ]);
    }

    public function listImages(array $filters = [], int $page = 1, int $pageSize = 50, string $sortBy = 'created_at', string $sortOrder = 'desc'): array
    {
        $cacheKey = sprintf('images.list.%s.%d.%d.%s.%s', md5(json_encode($filters)), $page, $pageSize, $sortBy, $sortOrder);

        $store = Cache::getStore();
        $supportsTags = $store instanceof \Illuminate\Cache\TaggableStore;
        $cache = $supportsTags ? Cache::tags(['images']) : Cache::store();

        return $cache->remember($cacheKey, $this->cacheTtl, function () use ($filters, $page, $pageSize, $sortBy, $sortOrder) {
            try {
                $response = $this->client()->get($this->baseUrl . '/api/v1/images', [
                    ...$filters,
                    'page' => $page,
                    'page_size' => $pageSize,
                    'sort_by' => $sortBy,
                    'sort_order' => $sortOrder,
                ]);

                if ($response->successful()) {
                    $json = $response->json();
                    $data = is_array($json) && array_key_exists('data', $json) ? $json['data'] : $json;
                    return [
                        'success' => true,
                        'data' => $data,
                        'error' => null,
                    ];
                }

                Log::channel('krai-images')->error('Failed to list images', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                ]);
            } catch (\Throwable $e) {
                Log::channel('krai-images')->error('Error listing images', ['exception' => $e]);
            }

            return ['success' => false, 'data' => [], 'error' => 'Failed to fetch images'];
        });
    }

    public function getImage(string $imageId, bool $includeRelations = false): array
    {
        try {
            $response = $this->client()->get($this->baseUrl . '/api/v1/images/' . $imageId, [
                'include_relations' => $includeRelations ? '1' : '0',
            ]);

            if ($response->successful()) {
                return ['success' => true, 'data' => $response->json(), 'error' => null];
            }

            Log::channel('krai-images')->error('Failed to get image', [
                'status' => $response->status(),
                'body' => $response->body(),
            ]);
        } catch (\Throwable $e) {
            Log::channel('krai-images')->error('Error getting image', ['exception' => $e]);
        }

        return ['success' => false, 'data' => null, 'error' => 'Failed to fetch image'];
    }

    public function getImagesByDocument(string $documentId, int $page = 1, int $pageSize = 50): array
    {
        $cacheKey = sprintf('images.by_document.%s.%d.%d', $documentId, $page, $pageSize);

        $store = Cache::getStore();
        $supportsTags = $store instanceof \Illuminate\Cache\TaggableStore;
        $cache = $supportsTags ? Cache::tags(['images']) : Cache::store();

        return $cache->remember($cacheKey, $this->cacheTtl, function () use ($documentId, $page, $pageSize) {
            try {
                $response = $this->client()->get($this->baseUrl . '/api/v1/images/by-document/' . $documentId, [
                    'page' => $page,
                    'page_size' => $pageSize,
                ]);

                if ($response->successful()) {
                    return ['success' => true, 'data' => $response->json(), 'error' => null];
                }

                Log::channel('krai-images')->error('Failed to get images by document', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                ]);
            } catch (\Throwable $e) {
                Log::channel('krai-images')->error('Error getting images by document', ['exception' => $e]);
            }

            return ['success' => false, 'data' => [], 'error' => 'Failed to fetch images by document'];
        });
    }

    public function getImageStats(): array
    {
        $cacheKey = 'images.stats';

        $store = Cache::getStore();
        $supportsTags = $store instanceof \Illuminate\Cache\TaggableStore;
        $cache = $supportsTags ? Cache::tags(['images']) : Cache::store();

        return $cache->remember($cacheKey, $this->statsCacheTtl, function () {
            try {
                $response = $this->client()->get($this->baseUrl . '/api/v1/images/stats');

                if ($response->successful()) {
                    return ['success' => true, 'data' => $response->json(), 'error' => null];
                }

                Log::channel('krai-images')->error('Failed to get image stats', [
                    'status' => $response->status(),
                    'body' => $response->body(),
                ]);
            } catch (\Throwable $e) {
                Log::channel('krai-images')->error('Error getting image stats', ['exception' => $e]);
            }

            return ['success' => false, 'data' => [], 'error' => 'Failed to fetch image stats'];
        });
    }

    public function deleteImage(string $imageId, bool $deleteFromStorage = false): array
    {
        try {
            $response = $this->client()->delete($this->baseUrl . '/api/v1/images/' . $imageId, [
                'delete_from_storage' => $deleteFromStorage ? '1' : '0',
            ]);

            if ($response->successful()) {
                $this->clearCache();
                return ['success' => true, 'data' => $response->json(), 'error' => null];
            }

            Log::channel('krai-images')->error('Failed to delete image', [
                'status' => $response->status(),
                'body' => $response->body(),
            ]);
        } catch (\Throwable $e) {
            Log::channel('krai-images')->error('Error deleting image', ['exception' => $e]);
        }

        return ['success' => false, 'data' => null, 'error' => 'Failed to delete image'];
    }

    public function bulkDeleteImages(array $imageIds, bool $deleteFromStorage = false): array
    {
        $summary = [
            'success' => 0,
            'failed' => 0,
            'errors' => [],
        ];

        foreach ($imageIds as $id) {
            $result = $this->deleteImage($id, $deleteFromStorage);
            if ($result['success']) {
                $summary['success']++;
            } else {
                $summary['failed']++;
                $summary['errors'][] = ['id' => $id, 'error' => $result['error']];
            }
        }

        $this->clearCache();

        return $summary;
    }

    public function downloadImage(string $imageId)
    {
        try {
            return $this->client()->get($this->baseUrl . '/api/v1/images/' . $imageId . '/download');
        } catch (\Throwable $e) {
            Log::channel('krai-images')->error('Error downloading image', ['exception' => $e]);
            return null;
        }
    }

    public function createBulkDownloadZip(array $imageIds): ?string
    {
        $zip = new \ZipArchive();
        $tmpPath = tempnam(sys_get_temp_dir(), 'images_zip_');
        if ($tmpPath === false) {
            return null;
        }

        if ($zip->open($tmpPath, \ZipArchive::OVERWRITE) !== true) {
            return null;
        }

        foreach ($imageIds as $id) {
            $response = $this->downloadImage($id);
            if (!$response || !$response->successful()) {
                Log::channel('krai-images')->warning('Skipping image in bulk download', ['id' => $id]);
                continue;
            }

            $content = $response->body();
            $filename = $id . '.bin';
            $disposition = $response->header('Content-Disposition');
            if ($disposition && preg_match('/filename="?([^";]+)"?/i', $disposition, $matches)) {
                $filename = trim($matches[1]);
            }

            $zip->addFromString($filename, $content);
        }

        $zip->close();

        return $tmpPath;
    }

    public function clearCache(): void
    {
        $store = Cache::getStore();
        if ($store instanceof \Illuminate\Cache\TaggableStore) {
            Cache::tags(['images'])->flush();
            return;
        }

        Cache::flush();
    }
}

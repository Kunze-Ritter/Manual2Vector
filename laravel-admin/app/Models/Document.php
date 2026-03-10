<?php

namespace App\Models;

use App\Enums\DocumentProcessingStatus;
use App\Models\Manufacturer;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Document extends Model
{
    protected $table = 'krai_core.documents';

    protected $keyType = 'string';

    public $incrementing = false;

    protected $fillable = [
        'filename',
        'file_size',
        'file_hash',
        'storage_path',
        'document_type',
        'language',
        'version',
        'publish_date',
        'page_count',
        'word_count',
        'character_count',
        'extracted_metadata',
        'processing_status',
        'processing_results',
        'processing_error',
        'stage_status',
        'confidence_score',
        'ocr_confidence',
        'manual_review_required',
        'manual_review_completed',
        'manual_review_notes',
        'manufacturer',
        'series',
        'models',
        'priority_level',
        'manufacturer_id',
    ];

    protected function casts(): array
    {
        return [
            'file_size' => 'integer',
            'publish_date' => 'date',
            'page_count' => 'integer',
            'word_count' => 'integer',
            'character_count' => 'integer',
            'extracted_metadata' => 'array',
            'processing_results' => 'array',
            'stage_status' => 'array',
            'confidence_score' => 'float',
            'ocr_confidence' => 'float',
            'manual_review_required' => 'boolean',
            'manual_review_completed' => 'boolean',
            'models' => 'array',
            'priority_level' => 'integer',
            'created_at' => 'datetime',
            'updated_at' => 'datetime',
            'processing_status' => DocumentProcessingStatus::class,
        ];
    }

    public function manufacturer(): BelongsTo
    {
        return $this->belongsTo(Manufacturer::class, 'manufacturer_id');
    }
}

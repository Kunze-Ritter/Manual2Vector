<?php

return [
    /*
    |--------------------------------------------------------------------------
    | KRAI Engine Configuration
    |--------------------------------------------------------------------------
    |
    | Configuration for the KRAI Engine FastAPI backend integration.
    | This includes the base URL, authentication token, and timeouts.
    |
    */

    'engine_url' => env('KRAI_ENGINE_URL', 'http://krai-engine:8000'),
    'service_jwt' => env('KRAI_ENGINE_SERVICE_JWT', ''),
    'default_timeout' => 120, // Default HTTP timeout in seconds
    'query_timeout' => 60, // Timeout for read-only queries

    /*
    |--------------------------------------------------------------------------
    | Stage Definitions
    |--------------------------------------------------------------------------
    |
    | Definition of all processing stages available in the KRAI pipeline.
    | Each stage includes a German label, description, icon, and grouping.
    |
    */

    'stages' => [
        'upload' => [
            'label' => 'Upload',
            'description' => 'Dokument hochladen und validieren',
            'icon' => 'heroicon-o-arrow-up-tray',
            'group' => 'initialization',
            'order' => 1
        ],
        'text_extraction' => [
            'label' => 'Text-Extraktion',
            'description' => 'Text aus PDF extrahieren',
            'icon' => 'heroicon-o-document-text',
            'group' => 'extraction',
            'order' => 2
        ],
        'table_extraction' => [
            'label' => 'Tabellen-Extraktion',
            'description' => 'Tabellen strukturiert extrahieren',
            'icon' => 'heroicon-o-table-cells',
            'group' => 'extraction',
            'order' => 3
        ],
        'svg_processing' => [
            'label' => 'SVG-Verarbeitung',
            'description' => 'Vektorgrafiken zu PNG konvertieren',
            'icon' => 'heroicon-o-photo',
            'group' => 'extraction',
            'order' => 4
        ],
        'image_processing' => [
            'label' => 'Bild-Verarbeitung',
            'description' => 'Bilder extrahieren und verarbeiten',
            'icon' => 'heroicon-o-photo',
            'group' => 'extraction',
            'order' => 5
        ],
        'visual_embedding' => [
            'label' => 'Visuelle Embeddings',
            'description' => 'Bild-Embeddings generieren',
            'icon' => 'heroicon-o-cube',
            'group' => 'enrichment',
            'order' => 6
        ],
        'link_extraction' => [
            'label' => 'Link-Extraktion',
            'description' => 'URLs und Referenzen extrahieren',
            'icon' => 'heroicon-o-link',
            'group' => 'extraction',
            'order' => 7
        ],
        'chunk_prep' => [
            'label' => 'Chunk-Vorbereitung',
            'description' => 'Text in Chunks aufteilen',
            'icon' => 'heroicon-o-squares-2x2',
            'group' => 'processing',
            'order' => 8
        ],
        'classification' => [
            'label' => 'Klassifizierung',
            'description' => 'Dokumenttyp und Hersteller erkennen',
            'icon' => 'heroicon-o-tag',
            'group' => 'processing',
            'order' => 9
        ],
        'metadata_extraction' => [
            'label' => 'Metadaten-Extraktion',
            'description' => 'Fehlercodes und Metadaten extrahieren',
            'icon' => 'heroicon-o-information-circle',
            'group' => 'processing',
            'order' => 10
        ],
        'parts_extraction' => [
            'label' => 'Ersatzteil-Extraktion',
            'description' => 'Ersatzteile und Artikelnummern extrahieren',
            'icon' => 'heroicon-o-wrench-screwdriver',
            'group' => 'processing',
            'order' => 11
        ],
        'series_detection' => [
            'label' => 'Serien-Erkennung',
            'description' => 'Produktserien erkennen',
            'icon' => 'heroicon-o-rectangle-stack',
            'group' => 'processing',
            'order' => 12
        ],
        'storage' => [
            'label' => 'Speicherung',
            'description' => 'Daten in Object Storage speichern',
            'icon' => 'heroicon-o-cloud-arrow-up',
            'group' => 'finalization',
            'order' => 13
        ],
        'embedding' => [
            'label' => 'Text-Embeddings',
            'description' => 'Text-Embeddings generieren',
            'icon' => 'heroicon-o-cube-transparent',
            'group' => 'enrichment',
            'order' => 14
        ],
        'search_indexing' => [
            'label' => 'Such-Indexierung',
            'description' => 'Suchindex aktualisieren',
            'icon' => 'heroicon-o-magnifying-glass',
            'group' => 'finalization',
            'order' => 15
        ]
    ],

    /*
    |--------------------------------------------------------------------------
    | Stage Groups
    |--------------------------------------------------------------------------
    |
    | Groups for organizing stages in the UI. Stages are grouped by their
    | processing phase to improve user experience and navigation.
    |
    */

    'stage_groups' => [
        'initialization',
        'extraction', 
        'processing',
        'enrichment',
        'finalization'
    ],

    /*
    |--------------------------------------------------------------------------
    | Default Stage Selection
    |--------------------------------------------------------------------------
    |
    | Default stages to process when no custom selection is made.
    | This excludes the UPLOAD stage which is handled separately.
    |
    */

    'default_stages' => [
        'text_extraction',
        'table_extraction',
        'svg_processing',
        'image_processing',
        'visual_embedding',
        'link_extraction',
        'chunk_prep',
        'classification',
        'metadata_extraction',
        'parts_extraction',
        'series_detection',
        'storage',
        'embedding',
        'search_indexing'
    ],
];

/*
|--------------------------------------------------------------------------
| Helper Functions
|--------------------------------------------------------------------------
|
| These functions provide convenient access to stage configuration
| throughout the application.
|
*/

if (!function_exists('krai_stages')) {
    /**
     * Get all KRAI stages
     */
    function krai_stages(): array
    {
        return config('krai.stages', []);
    }
}

if (!function_exists('krai_stage_label')) {
    /**
     * Get the German label for a stage
     */
    function krai_stage_label(string $stage): string
    {
        return config("krai.stages.{$stage}.label", $stage);
    }
}

if (!function_exists('krai_stage_icon')) {
    /**
     * Get the icon for a stage
     */
    function krai_stage_icon(string $stage): string
    {
        return config("krai.stages.{$stage}.icon", 'heroicon-o-cog');
    }
}

if (!function_exists('krai_stage_group')) {
    /**
     * Get the group for a stage
     */
    function krai_stage_group(string $stage): string
    {
        return config("krai.stages.{$stage}.group", 'processing');
    }
}

if (!function_exists('krai_stages_by_group')) {
    /**
     * Get stages grouped by their group
     */
    function krai_stages_by_group(): array
    {
        $stages = krai_stages();
        $groups = [];
        
        foreach ($stages as $key => $stage) {
            $group = $stage['group'];
            $groups[$group][$key] = $stage;
        }
        
        return $groups;
    }
}

if (!function_exists('krai_stage_options')) {
    /**
     * Get stages formatted for form select options
     */
    function krai_stage_options(): array
    {
        $stages = krai_stages();
        $options = [];
        
        foreach ($stages as $key => $stage) {
            $options[$key] = $stage['label'];
        }
        
        return $options;
    }
}

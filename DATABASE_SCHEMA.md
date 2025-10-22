# KRAI Database Schema Documentation
================================================================================

**Zuletzt aktualisiert:** 22.10.2025 um 10:45 Uhr

**Quelle:** Direkt aus Supabase (ECHTE Struktur)

## ⚠️ WICHTIGE INFORMATIONEN

### Embeddings Storage
- **Embeddings sind in `krai_intelligence.chunks` als Spalte `embedding` gespeichert!**
- Es gibt KEIN separates `krai_embeddings` Schema
- Spalte: `embedding` (Typ: `vector(768)`)

### View Naming Convention
- Alle Views nutzen `vw_` Prefix
- Views sind im `public` Schema
- Tabellen sind in `krai_*` Schemas

### Wichtige Tabellen für Processing
- `krai_core.documents` - Haupttabelle für Dokumente
- `krai_core.products` - Produkte
- `krai_core.manufacturers` - Hersteller
- `krai_intelligence.chunks` - Text-Chunks mit Embeddings
- `krai_intelligence.error_codes` - Fehlercodes
- `krai_content.videos` - Videos
- `krai_content.links` - Links
- `krai_content.images` - Bilder
- `krai_parts.parts_catalog` - Ersatzteile

---

## Table of Contents

- [krai_agent](#krai-agent) (2 Tabellen)
- [krai_config](#krai-config) (4 Tabellen)
- [krai_content](#krai-content) (5 Tabellen)
- [krai_core](#krai-core) (12 Tabellen)
- [krai_integrations](#krai-integrations) (2 Tabellen)
- [krai_intelligence](#krai-intelligence) (11 Tabellen)
- [krai_ml](#krai-ml) (2 Tabellen)
- [krai_parts](#krai-parts) (2 Tabellen)
- [krai_service](#krai-service) (3 Tabellen)
- [krai_system](#krai-system) (5 Tabellen)
- [krai_users](#krai-users) (2 Tabellen)

---

## krai_agent

### krai_agent.memory

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `session_id` | character varying(255) | NO | - |
| `role` | character varying(50) | NO | 'technician'::character varying |
| `content` | text | NO | - |
| `metadata` | jsonb | NO | '{}'::jsonb |
| `tokens_used` | int4 | NO | 0 |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `message` | text | NO | ''::text |

### krai_agent.message

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | int4 | NO | nextval('krai_agent.message_id_seq'::... |
| `session_id` | character varying(255) | NO | - |
| `message` | jsonb | NO | - |

## krai_config

### krai_config.competition_analysis

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `our_product_id` | uuid | NO | - |
| `competitor_manufacturer_id` | uuid | NO | - |
| `competitor_model_name` | character varying(200) | YES | - |
| `comparison_category` | character varying(100) | YES | - |
| `our_advantage` | text | YES | - |
| `competitor_advantage` | text | YES | - |
| `feature_comparison` | jsonb | YES | '{}'::jsonb |
| `price_comparison` | jsonb | YES | '{}'::jsonb |
| `market_position` | character varying(50) | YES | - |
| `created_at` | timestamptz | YES | now() |

### krai_config.option_groups

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `manufacturer_id` | uuid | NO | - |
| `group_name` | character varying(100) | NO | - |
| `group_description` | text | YES | - |
| `display_order` | int4 | YES | 0 |
| `is_required` | bool | YES | false |
| `created_at` | timestamptz | YES | now() |

### krai_config.product_compatibility

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `base_product_id` | uuid | NO | - |
| `option_product_id` | uuid | NO | - |
| `compatibility_type` | character varying(50) | YES | 'compatible'::character varying |
| `compatibility_notes` | text | YES | - |
| `validated_date` | date | YES | - |
| `validation_status` | character varying(20) | YES | 'pending'::character varying |
| `created_at` | timestamptz | YES | now() |

### krai_config.product_features

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `product_id` | uuid | NO | - |
| `feature_id` | uuid | NO | - |
| `feature_value` | text | YES | - |
| `is_standard` | bool | YES | true |
| `additional_cost_usd` | numeric | YES | 0.00 |
| `created_at` | timestamptz | YES | now() |

## krai_content

### krai_content.images

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `document_id` | uuid | YES | - |
| `chunk_id` | uuid | YES | - |
| `filename` | character varying(255) | YES | - |
| `original_filename` | character varying(255) | YES | - |
| `storage_path` | text | YES | - |
| `storage_url` | text | NO | - |
| `file_size` | int4 | YES | - |
| `image_format` | character varying(10) | YES | - |
| `width_px` | int4 | YES | - |
| `height_px` | int4 | YES | - |
| `page_number` | int4 | YES | - |
| `image_index` | int4 | YES | - |
| `image_type` | character varying(50) | YES | - |
| `ai_description` | text | YES | - |
| `ai_confidence` | numeric | YES | - |
| `contains_text` | bool | YES | false |
| `ocr_text` | text | YES | - |
| `ocr_confidence` | numeric | YES | - |
| `manual_description` | text | YES | - |
| `tags` | _text | YES | - |
| `file_hash` | character varying(64) | YES | - |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `figure_number` | character varying(50) | YES | - |
| `figure_context` | text | YES | - |

### krai_content.links

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `document_id` | uuid | NO | - |
| `url` | text | NO | - |
| `link_type` | character varying(50) | NO | 'external'::character varying |
| `page_number` | int4 | NO | - |
| `description` | text | YES | - |
| `position_data` | jsonb | YES | - |
| `is_active` | bool | YES | true |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `video_id` | uuid | YES | - |
| `metadata` | jsonb | YES | '{}'::jsonb |
| `link_category` | character varying(50) | YES | - |
| `confidence_score` | numeric | YES | 0.0 |
| `manufacturer_id` | uuid | YES | - |
| `series_id` | uuid | YES | - |
| `related_error_codes` | _text | YES | - |

### krai_content.print_defects

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `manufacturer_id` | uuid | NO | - |
| `product_id` | uuid | YES | - |
| `original_image_id` | uuid | YES | - |
| `defect_name` | character varying(100) | NO | - |
| `defect_category` | character varying(50) | YES | - |
| `defect_description` | text | YES | - |
| `example_image_url` | text | YES | - |
| `annotated_image_url` | text | YES | - |
| `detection_confidence` | numeric | YES | - |
| `common_causes` | jsonb | YES | '[]'::jsonb |
| `recommended_solutions` | jsonb | YES | '[]'::jsonb |
| `related_error_codes` | _text | YES | - |
| `created_at` | timestamptz | YES | now() |

### krai_content.video_products

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `video_id` | uuid | NO | - |
| `product_id` | uuid | NO | - |
| `created_at` | timestamptz | YES | now() |

### krai_content.videos

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `link_id` | uuid | YES | - |
| `youtube_id` | character varying(20) | YES | - |
| `platform` | character varying(20) | YES | - |
| `video_url` | text | YES | - |
| `title` | character varying(500) | NO | - |
| `description` | text | YES | - |
| `thumbnail_url` | text | YES | - |
| `duration` | int4 | YES | - |
| `view_count` | int8 | YES | - |
| `like_count` | int4 | YES | - |
| `comment_count` | int4 | YES | - |
| `channel_id` | character varying(50) | YES | - |
| `channel_title` | character varying(200) | YES | - |
| `published_at` | timestamptz | YES | - |
| `manufacturer_id` | uuid | YES | - |
| `series_id` | uuid | YES | - |
| `document_id` | uuid | YES | - |
| `metadata` | jsonb | YES | - |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `enriched_at` | timestamptz | YES | now() |

## krai_core

### krai_core.document_products

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `document_id` | uuid | NO | - |
| `product_id` | uuid | NO | - |
| `is_primary_product` | bool | YES | false |
| `confidence_score` | numeric | YES | 0.80 |
| `extraction_method` | character varying(50) | YES | - |
| `page_numbers` | _int4 | YES | - |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |

### krai_core.document_relationships

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `primary_document_id` | uuid | NO | - |
| `secondary_document_id` | uuid | NO | - |
| `relationship_type` | character varying(50) | NO | - |
| `relationship_strength` | numeric | YES | 0.5 |
| `auto_discovered` | bool | YES | true |
| `manual_verification` | bool | YES | false |
| `verification_date` | timestamptz | YES | - |
| `verified_by` | character varying(100) | YES | - |
| `notes` | text | YES | - |
| `created_at` | timestamptz | YES | now() |

### krai_core.documents

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `filename` | character varying(255) | NO | - |
| `file_size` | int8 | YES | - |
| `file_hash` | character varying(64) | YES | - |
| `storage_path` | text | YES | - |
| `document_type` | character varying(100) | YES | - |
| `language` | character varying(10) | YES | 'en'::character varying |
| `version` | character varying(50) | YES | - |
| `publish_date` | date | YES | - |
| `page_count` | int4 | YES | - |
| `word_count` | int4 | YES | - |
| `character_count` | int4 | YES | - |
| `extracted_metadata` | jsonb | YES | '{}'::jsonb |
| `processing_status` | character varying(50) | YES | 'pending'::character varying |
| `processing_results` | jsonb | YES | - |
| `processing_error` | text | YES | - |
| `stage_status` | jsonb | YES | '{}'::jsonb |
| `confidence_score` | numeric | YES | - |
| `ocr_confidence` | numeric | YES | - |
| `manual_review_required` | bool | YES | false |
| `manual_review_completed` | bool | YES | false |
| `manual_review_notes` | text | YES | - |
| `manufacturer` | character varying(100) | YES | - |
| `series` | character varying(100) | YES | - |
| `models` | _text | YES | - |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `priority_level` | int4 | YES | 5 |
| `manufacturer_id` | uuid | YES | - |

**Note:** Spalten `original_filename`, `content_text`, und `content_summary` wurden in Migration 104 entfernt.

### krai_core.manufacturers

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `name` | character varying(100) | NO | - |
| `short_name` | character varying(10) | YES | - |
| `country` | character varying(50) | YES | - |
| `founded_year` | int4 | YES | - |
| `website` | character varying(255) | YES | - |
| `support_email` | character varying(255) | YES | - |
| `support_phone` | character varying(50) | YES | - |
| `logo_url` | text | YES | - |
| `is_competitor` | bool | YES | false |
| `market_share_percent` | numeric | YES | - |
| `annual_revenue_usd` | int8 | YES | - |
| `employee_count` | int4 | YES | - |
| `headquarters_address` | text | YES | - |
| `stock_symbol` | character varying(10) | YES | - |
| `primary_business_segment` | character varying(100) | YES | - |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |

### krai_core.oem_relationships

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `brand_manufacturer` | character varying(100) | NO | - |
| `brand_series_pattern` | character varying(200) | NO | - |
| `oem_manufacturer` | character varying(100) | NO | - |
| `relationship_type` | character varying(50) | YES | 'engine'::character varying |
| `applies_to` | _text | YES | ARRAY['error_codes'::text, 'parts'::t... |
| `notes` | text | YES | - |
| `confidence` | float8 | YES | 1.0 |
| `source` | character varying(100) | YES | 'manual'::character varying |
| `verified` | bool | YES | false |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |

### krai_core.product_accessories

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `product_id` | uuid | NO | - |
| `accessory_id` | uuid | NO | - |
| `compatibility_type` | character varying(50) | NO | - |
| `installation_required` | bool | YES | false |
| `quantity_min` | int4 | YES | 1 |
| `quantity_max` | int4 | YES | 1 |
| `notes` | text | YES | - |
| `created_at` | timestamptz | YES | now() |
| `priority` | int4 | YES | 0 |
| `compatibility_notes` | text | YES | - |
| `is_standard` | bool | YES | false |

### krai_core.product_configurations

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `configuration_name` | character varying(200) | YES | - |
| `base_product_id` | uuid | NO | - |
| `accessories` | jsonb | YES | '[]'::jsonb |
| `is_valid` | bool | YES | true |
| `validation_errors` | jsonb | YES | '[]'::jsonb |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `created_by` | character varying(100) | YES | - |

### krai_core.product_series

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `manufacturer_id` | uuid | NO | - |
| `series_name` | character varying(100) | NO | - |
| `series_code` | character varying(50) | YES | - |
| `launch_date` | date | YES | - |
| `end_of_life_date` | date | YES | - |
| `target_market` | character varying(100) | YES | - |
| `price_range` | character varying(50) | YES | - |
| `key_features` | jsonb | YES | '{}'::jsonb |
| `series_description` | text | YES | - |
| `marketing_name` | character varying(150) | YES | - |
| `successor_series_id` | uuid | YES | - |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `model_pattern` | text | YES | - |

### krai_core.products

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `manufacturer_id` | uuid | YES | - |
| `series_id` | uuid | YES | - |
| `model_number` | character varying(100) | NO | - |
| `product_type` | character varying(50) | NO | 'printer'::character varying |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `specifications` | jsonb | YES | '{}'::jsonb |
| `pricing` | jsonb | YES | '{}'::jsonb |
| `lifecycle` | jsonb | YES | '{}'::jsonb |
| `urls` | jsonb | YES | '{}'::jsonb |
| `metadata` | jsonb | YES | '{}'::jsonb |
| `oem_manufacturer` | character varying(100) | YES | - |
| `oem_relationship_type` | character varying(50) | YES | - |
| `oem_notes` | text | YES | - |

### krai_core.products_backup

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | YES | - |
| `parent_id` | uuid | YES | - |
| `manufacturer_id` | uuid | YES | - |
| `series_id` | uuid | YES | - |
| `model_number` | character varying(100) | YES | - |
| `model_name` | character varying(200) | YES | - |
| `product_type` | character varying(50) | YES | - |
| `launch_date` | date | YES | - |
| `end_of_life_date` | date | YES | - |
| `msrp_usd` | numeric | YES | - |
| `weight_kg` | numeric | YES | - |
| `dimensions_mm` | jsonb | YES | - |
| `color_options` | _text | YES | - |
| `connectivity_options` | _text | YES | - |
| `print_technology` | character varying(50) | YES | - |
| `max_print_speed_ppm` | int4 | YES | - |
| `max_resolution_dpi` | int4 | YES | - |
| `max_paper_size` | character varying(20) | YES | - |
| `duplex_capable` | bool | YES | - |
| `network_capable` | bool | YES | - |
| `mobile_print_support` | bool | YES | - |
| `supported_languages` | _text | YES | - |
| `energy_star_certified` | bool | YES | - |
| `warranty_months` | int4 | YES | - |
| `service_manual_url` | text | YES | - |
| `parts_catalog_url` | text | YES | - |
| `driver_download_url` | text | YES | - |
| `firmware_version` | character varying(50) | YES | - |
| `option_dependencies` | jsonb | YES | - |
| `replacement_parts` | jsonb | YES | - |
| `common_issues` | jsonb | YES | - |
| `created_at` | timestamptz | YES | - |
| `updated_at` | timestamptz | YES | - |

### krai_core.products_with_names

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | YES | - |
| `manufacturer_id` | uuid | YES | - |
| `series_id` | uuid | YES | - |
| `model_number` | character varying(100) | YES | - |
| `product_type` | character varying(50) | YES | - |
| `created_at` | timestamptz | YES | - |
| `updated_at` | timestamptz | YES | - |
| `specifications` | jsonb | YES | - |
| `pricing` | jsonb | YES | - |
| `lifecycle` | jsonb | YES | - |
| `urls` | jsonb | YES | - |
| `metadata` | jsonb | YES | - |
| `manufacturer_name` | character varying(100) | YES | - |
| `series_name` | character varying(100) | YES | - |

### krai_core.public_products

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | YES | - |
| `manufacturer_id` | uuid | YES | - |
| `series_id` | uuid | YES | - |
| `model_number` | character varying(100) | YES | - |
| `product_type` | character varying(50) | YES | - |
| `created_at` | timestamptz | YES | - |
| `updated_at` | timestamptz | YES | - |
| `specifications` | jsonb | YES | - |
| `pricing` | jsonb | YES | - |
| `lifecycle` | jsonb | YES | - |
| `urls` | jsonb | YES | - |
| `metadata` | jsonb | YES | - |
| `manufacturer_name` | character varying(100) | YES | - |
| `series_name` | character varying(100) | YES | - |

## krai_integrations

### krai_integrations.api_keys

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `service_name` | character varying(100) | NO | - |
| `api_key_encrypted` | text | NO | - |
| `is_active` | bool | YES | true |
| `created_at` | timestamptz | YES | now() |

### krai_integrations.webhook_logs

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `webhook_url` | text | NO | - |
| `request_payload` | jsonb | YES | - |
| `response_status` | int4 | YES | - |
| `response_body` | text | YES | - |
| `processed_at` | timestamptz | YES | now() |

## krai_intelligence

### krai_intelligence.agent_performance

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `date` | date | YES | - |
| `tool_name` | text | YES | - |
| `total_calls` | int8 | YES | - |
| `successful_calls` | int8 | YES | - |
| `failed_calls` | int8 | YES | - |
| `avg_response_time_ms` | numeric | YES | - |
| `p95_response_time_ms` | float8 | YES | - |
| `avg_results_count` | numeric | YES | - |

### krai_intelligence.chunks

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `document_id` | uuid | NO | - |
| `text_chunk` | text | NO | - |
| `chunk_index` | int4 | NO | - |
| `page_start` | int4 | YES | - |
| `page_end` | int4 | YES | - |
| `processing_status` | character varying(20) | YES | 'pending'::character varying |
| `fingerprint` | character varying(64) | NO | - |
| `metadata` | jsonb | YES | '{}'::jsonb |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |
| `embedding` | vector | YES | - |

### krai_intelligence.error_code_images

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | gen_random_uuid() |
| `error_code_id` | uuid | NO | - |
| `image_id` | uuid | NO | - |
| `match_method` | text | YES | - |
| `match_confidence` | float8 | YES | 0.5 |
| `display_order` | int4 | YES | 0 |
| `created_at` | timestamptz | YES | now() |

### krai_intelligence.error_code_parts

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `error_code_id` | uuid | NO | - |
| `part_id` | uuid | NO | - |
| `relevance_score` | float8 | YES | 1.0 |
| `extraction_source` | text | YES | - |
| `created_at` | timestamptz | YES | now() |

### krai_intelligence.error_codes

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `chunk_id` | uuid | YES | - |
| `document_id` | uuid | YES | - |
| `manufacturer_id` | uuid | YES | - |
| `error_code` | character varying(20) | NO | - |
| `error_description` | text | YES | - |
| `solution_text` | text | YES | - |
| `page_number` | int4 | YES | - |
| `confidence_score` | numeric | YES | - |
| `extraction_method` | character varying(50) | YES | - |
| `requires_technician` | bool | YES | false |
| `requires_parts` | bool | YES | false |
| `estimated_fix_time_minutes` | int4 | YES | - |
| `severity_level` | character varying(20) | YES | - |
| `created_at` | timestamptz | YES | now() |
| `image_id` | uuid | YES | - |
| `context_text` | text | YES | - |
| `metadata` | jsonb | YES | '{}'::jsonb |
| `product_id` | uuid | YES | - |
| `video_id` | uuid | YES | - |

### krai_intelligence.feedback

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `session_id` | text | NO | - |
| `message_id` | text | YES | - |
| `rating` | int4 | YES | - |
| `feedback_type` | text | YES | - |
| `comment` | text | YES | - |
| `created_at` | timestamptz | YES | now() |

### krai_intelligence.product_research_cache

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `manufacturer` | character varying(100) | NO | - |
| `model_number` | character varying(100) | NO | - |
| `series_name` | character varying(200) | YES | - |
| `series_description` | text | YES | - |
| `specifications` | jsonb | YES | '{}'::jsonb |
| `physical_specs` | jsonb | YES | '{}'::jsonb |
| `oem_manufacturer` | character varying(100) | YES | - |
| `oem_relationship_type` | character varying(50) | YES | - |
| `oem_notes` | text | YES | - |
| `launch_date` | date | YES | - |
| `eol_date` | date | YES | - |
| `pricing` | jsonb | YES | '{}'::jsonb |
| `product_type` | character varying(100) | YES | - |
| `confidence` | float8 | YES | 0.0 |
| `source_urls` | _text | YES | - |
| `research_date` | timestamptz | YES | now() |
| `cache_valid_until` | timestamptz | YES | - |
| `verified` | bool | YES | false |
| `verified_by` | character varying(100) | YES | - |
| `verified_at` | timestamptz | YES | - |
| `notes` | text | YES | - |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |

### krai_intelligence.search_analytics

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `search_query` | text | NO | - |
| `search_type` | character varying(50) | YES | - |
| `results_count` | int4 | YES | - |
| `click_through_rate` | numeric | YES | - |
| `user_satisfaction_rating` | int4 | YES | - |
| `search_duration_ms` | int4 | YES | - |
| `result_relevance_scores` | jsonb | YES | - |
| `user_session_id` | character varying(100) | YES | - |
| `user_id` | uuid | YES | - |
| `manufacturer_filter` | uuid | YES | - |
| `product_filter` | uuid | YES | - |
| `document_type_filter` | character varying(100) | YES | - |
| `language_filter` | character varying(10) | YES | - |
| `created_at` | timestamptz | YES | now() |

### krai_intelligence.session_context

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `session_id` | text | NO | - |
| `context_type` | text | NO | - |
| `context_value` | text | NO | - |
| `confidence` | float8 | YES | 1.0 |
| `first_mentioned_at` | timestamptz | YES | now() |
| `last_used_at` | timestamptz | YES | now() |
| `use_count` | int4 | YES | 1 |

### krai_intelligence.tool_usage

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `session_id` | text | NO | - |
| `tool_name` | text | NO | - |
| `query_params` | jsonb | YES | - |
| `results_count` | int4 | YES | - |
| `response_time_ms` | int4 | YES | - |
| `success` | bool | YES | true |
| `error_message` | text | YES | - |
| `created_at` | timestamptz | YES | now() |

### krai_intelligence.user_satisfaction

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `date` | date | YES | - |
| `total_feedback` | int8 | YES | - |
| `avg_rating` | numeric | YES | - |
| `positive_feedback` | int8 | YES | - |
| `negative_feedback` | int8 | YES | - |
| `helpful_count` | int8 | YES | - |
| `not_helpful_count` | int8 | YES | - |
| `incorrect_count` | int8 | YES | - |

## krai_ml

### krai_ml.model_performance_history

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `model_id` | uuid | NO | - |
| `accuracy_score` | numeric | YES | - |
| `precision_score` | numeric | YES | - |
| `recall_score` | numeric | YES | - |
| `f1_score` | numeric | YES | - |
| `evaluated_at` | timestamptz | YES | now() |

### krai_ml.model_registry

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `model_name` | character varying(100) | NO | - |
| `model_version` | character varying(50) | NO | - |
| `model_type` | character varying(50) | NO | - |
| `framework` | character varying(50) | YES | - |
| `created_at` | timestamptz | YES | now() |

## krai_parts

### krai_parts.inventory_levels

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `part_id` | uuid | NO | - |
| `warehouse_location` | character varying(100) | YES | - |
| `current_stock` | int4 | YES | 0 |
| `minimum_stock_level` | int4 | YES | 0 |
| `maximum_stock_level` | int4 | YES | 1000 |
| `last_updated` | timestamptz | YES | now() |

### krai_parts.parts_catalog

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `manufacturer_id` | uuid | NO | - |
| `part_number` | character varying(100) | NO | - |
| `part_name` | character varying(255) | YES | - |
| `part_description` | text | YES | - |
| `part_category` | character varying(100) | YES | - |
| `unit_price_usd` | numeric | YES | - |
| `created_at` | timestamptz | YES | now() |

## krai_service

### krai_service.service_calls

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `manufacturer_id` | uuid | NO | - |
| `product_id` | uuid | YES | - |
| `assigned_technician_id` | uuid | YES | - |
| `call_status` | character varying(50) | YES | 'open'::character varying |
| `priority_level` | int4 | YES | 3 |
| `created_at` | timestamptz | YES | now() |
| `customer_name` | character varying(255) | YES | - |
| `customer_contact` | text | YES | - |
| `issue_description` | text | YES | - |
| `scheduled_date` | timestamptz | YES | - |
| `completed_date` | timestamptz | YES | - |
| `updated_at` | timestamptz | YES | now() |

### krai_service.service_history

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `service_call_id` | uuid | YES | - |
| `performed_by` | uuid | YES | - |
| `service_date` | timestamptz | YES | - |
| `service_notes` | text | YES | - |
| `parts_used` | jsonb | YES | '[]'::jsonb |
| `labor_hours` | numeric | YES | - |
| `created_at` | timestamptz | YES | now() |
| `service_type` | character varying(50) | YES | - |
| `outcome` | character varying(100) | YES | - |
| `updated_at` | timestamptz | YES | now() |

### krai_service.technicians

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `user_id` | uuid | YES | - |
| `technician_name` | character varying(255) | NO | - |
| `employee_id` | character varying(50) | YES | - |
| `email` | character varying(255) | YES | - |
| `phone` | character varying(50) | YES | - |
| `certification_level` | character varying(50) | YES | - |
| `specializations` | _text | YES | - |
| `is_active` | bool | YES | true |
| `hired_date` | date | YES | - |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |

## krai_system

### krai_system.audit_log

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `table_name` | character varying(100) | NO | - |
| `record_id` | uuid | NO | - |
| `operation` | character varying(10) | NO | - |
| `old_values` | jsonb | YES | - |
| `new_values` | jsonb | YES | - |
| `changed_by` | character varying(100) | YES | - |
| `changed_at` | timestamptz | YES | now() |
| `session_id` | character varying(100) | YES | - |
| `ip_address` | inet | YES | - |
| `user_agent` | text | YES | - |

### krai_system.health_checks

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `service_name` | character varying(100) | NO | - |
| `check_type` | character varying(50) | NO | - |
| `status` | character varying(20) | NO | - |
| `response_time_ms` | int4 | YES | - |
| `error_message` | text | YES | - |
| `details` | jsonb | YES | '{}'::jsonb |
| `checked_at` | timestamptz | YES | now() |

### krai_system.processing_queue

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `document_id` | uuid | YES | - |
| `chunk_id` | uuid | YES | - |
| `image_id` | uuid | YES | - |
| `video_id` | uuid | YES | - |
| `task_type` | character varying(50) | NO | - |
| `priority` | int4 | YES | 5 |
| `status` | character varying(20) | YES | 'pending'::character varying |
| `scheduled_at` | timestamptz | YES | now() |
| `started_at` | timestamptz | YES | - |
| `completed_at` | timestamptz | YES | - |
| `error_message` | text | YES | - |
| `retry_count` | int4 | YES | 0 |
| `max_retries` | int4 | YES | 3 |
| `created_at` | timestamptz | YES | now() |

### krai_system.stage_tracking

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `document_id` | uuid | YES | - |
| `stage_name` | character varying(100) | NO | - |
| `status` | character varying(50) | NO | - |
| `started_at` | timestamptz | YES | now() |
| `completed_at` | timestamptz | YES | - |
| `error_message` | text | YES | - |
| `metadata` | jsonb | YES | '{}'::jsonb |
| `created_at` | timestamptz | YES | now() |
| `updated_at` | timestamptz | YES | now() |

### krai_system.system_metrics

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `metric_name` | character varying(100) | NO | - |
| `metric_value` | numeric | YES | - |
| `metric_unit` | character varying(20) | YES | - |
| `metric_category` | character varying(50) | YES | - |
| `collection_timestamp` | timestamptz | YES | now() |
| `server_instance` | character varying(100) | YES | - |
| `additional_context` | jsonb | YES | '{}'::jsonb |

## krai_users

### krai_users.user_sessions

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `user_id` | uuid | NO | - |
| `session_token` | character varying(255) | NO | - |
| `expires_at` | timestamptz | NO | - |
| `created_at` | timestamptz | YES | now() |

### krai_users.users

| Spalte | Typ | Nullable | Default |
|--------|-----|----------|---------|
| `id` | uuid | NO | uuid_generate_v4() |
| `preferred_manufacturer_id` | uuid | YES | - |
| `username` | character varying(100) | NO | - |
| `email` | character varying(255) | NO | - |
| `role` | character varying(50) | YES | 'user'::character varying |
| `created_at` | timestamptz | YES | now() |

---

## Public Views (vw_*)

Alle Views nutzen `vw_` Prefix und zeigen auf Tabellen in krai_* Schemas:

| View | Zeigt auf | Hinweis |
|------|-----------|---------|
| `vw_agent_memory` | `krai_agent.memory` | - |
| `vw_audit_log` | `krai_system.audit_log` | - |
| `vw_chunks` | `krai_intelligence.chunks` | ⚠️ Enthält embedding Spalte! |
| `vw_document_products` | `krai_core.document_products` | - |
| `vw_documents` | `krai_core.documents` | - |
| `vw_embeddings` | `ALIAS für vw_chunks` | ⚠️ Embeddings sind IN chunks! |
| `vw_error_codes` | `krai_intelligence.error_codes` | - |
| `vw_images` | `krai_content.images` | - |
| `vw_intelligence_chunks` | `krai_intelligence.chunks` | - |
| `vw_links` | `krai_content.links` | - |
| `vw_manufacturers` | `krai_core.manufacturers` | - |
| `vw_parts` | `krai_parts.parts_catalog` | - |
| `vw_processing_queue` | `krai_system.processing_queue` | - |
| `vw_product_series` | `krai_core.product_series` | - |
| `vw_products` | `krai_core.products` | - |
| `vw_search_analytics` | `krai_intelligence.search_analytics` | - |
| `vw_system_metrics` | `krai_system.system_metrics` | - |
| `vw_video_products` | `krai_content.video_products` | - |
| `vw_videos` | `krai_content.videos` | - |
| `vw_webhook_logs` | `krai_integrations.webhook_logs` | - |

---

## Statistik

- **Schemas:** 11
- **Tabellen:** 50
- **Spalten:** 583

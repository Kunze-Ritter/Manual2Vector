# KRAI Database Schema Documentation
================================================================================

**Zuletzt aktualisiert:** 17.10.2025 um 10:47 Uhr

**Quelle:** Generiert aus SQL Migration Files

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

- [krai_agent](#krai-agent) (4 Tabellen)
- [krai_config](#krai-config) (4 Tabellen)
- [krai_content](#krai-content) (7 Tabellen)
- [krai_core](#krai-core) (8 Tabellen)
- [krai_integrations](#krai-integrations) (2 Tabellen)
- [krai_intelligence](#krai-intelligence) (7 Tabellen)
- [krai_ml](#krai-ml) (2 Tabellen)
- [krai_parts](#krai-parts) (2 Tabellen)
- [krai_service](#krai-service) (3 Tabellen)
- [krai_system](#krai-system) (5 Tabellen)
- [krai_users](#krai-users) (2 Tabellen)

---

## krai_agent

### krai_agent.feedback

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `session_id` | TEXT NOT NULL |
| `message_id` | TEXT |
| `rating` | INTEGER |
| `feedback_type` | TEXT |
| `comment` | TEXT |
| `created_at` | TIMESTAMPTZ DEFAULT NOW() |

### krai_agent.memory

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4() |
| `session_id` | VARCHAR(255) NOT NULL |
| `role` | VARCHAR(50) NOT NULL |
| `content` | TEXT NOT NULL |
| `metadata` | JSONB DEFAULT '{}'::jsonb |
| `tokens_used` | INTEGER DEFAULT 0 |
| `created_at` | TIMESTAMPTZ DEFAULT now() |
| `updated_at` | TIMESTAMPTZ DEFAULT now() |

### krai_agent.session_context

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `session_id` | TEXT NOT NULL |
| `context_type` | TEXT NOT NULL |
| `context_value` | TEXT NOT NULL |
| `confidence` | FLOAT DEFAULT 1.0 |
| `first_mentioned_at` | TIMESTAMPTZ DEFAULT NOW() |
| `last_used_at` | TIMESTAMPTZ DEFAULT NOW() |
| `use_count` | INTEGER DEFAULT 1 |

### krai_agent.tool_usage

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `session_id` | TEXT NOT NULL |
| `tool_name` | TEXT NOT NULL |
| `query_params` | JSONB |
| `results_count` | INTEGER |
| `response_time_ms` | INTEGER |
| `success` | BOOLEAN DEFAULT true |
| `error_message` | TEXT |
| `created_at` | TIMESTAMPTZ DEFAULT NOW() |

## krai_config

### krai_config.competition_analysis

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `our_product_id` | UUID NOT NULL → krai_core.products |
| `competitor_manufacturer_id` | UUID NOT NULL → krai_core.manufacturers |
| `competitor_model_name` | VARCHAR(200) |
| `comparison_category` | VARCHAR(100) |
| `our_advantage` | TEXT |
| `competitor_advantage` | TEXT |
| `feature_comparison` | JSONB DEFAULT '{}' |
| `price_comparison` | JSONB DEFAULT '{}' |
| `market_position` | VARCHAR(50) |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_config.option_groups

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `manufacturer_id` | UUID NOT NULL → krai_core.manufacturers |
| `group_name` | VARCHAR(100) NOT NULL |
| `group_description` | TEXT |
| `display_order` | INTEGER DEFAULT 0 |
| `is_required` | BOOLEAN DEFAULT false |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_config.product_compatibility

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `base_product_id` | UUID NOT NULL → krai_core.products |
| `option_product_id` | UUID NOT NULL → krai_core.products |
| `compatibility_type` | VARCHAR(50) DEFAULT 'compatible' |
| `compatibility_notes` | TEXT |
| `validated_date` | DATE |
| `validation_status` | VARCHAR(20) DEFAULT 'pending' |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_config.product_features

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `product_id` | UUID NOT NULL → krai_core.products |
| `feature_id` | UUID NOT NULL → krai_config.option_groups |
| `feature_value` | TEXT |
| `is_standard` | BOOLEAN DEFAULT true |
| `additional_cost_usd` | DECIMAL(10,2) DEFAULT 0.00 |
| `created_at` | TIMESTAMP DEFAULT NOW() |

## krai_content

### krai_content.chunks

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `document_id` | UUID NOT NULL → krai_core.documents |
| `content` | TEXT NOT NULL |
| `chunk_type` | VARCHAR(50) DEFAULT 'text' |
| `chunk_index` | INTEGER NOT NULL |
| `page_number` | INTEGER |
| `section_title` | VARCHAR(255) |
| `confidence_score` | DECIMAL(3,2) |
| `language` | VARCHAR(10) DEFAULT 'en' |
| `processing_notes` | TEXT |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_content.images

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `document_id` | UUID → krai_core.documents |
| `chunk_id` | UUID → krai_content.chunks |
| `filename` | VARCHAR(255) |
| `original_filename` | VARCHAR(255) |
| `storage_path` | TEXT |
| `storage_url` | TEXT NOT NULL |
| `file_size` | INTEGER |
| `image_format` | VARCHAR(10) |
| `width_px` | INTEGER |
| `height_px` | INTEGER |
| `page_number` | INTEGER |
| `image_index` | INTEGER |
| `image_type` | VARCHAR(50) |
| `ai_description` | TEXT |
| `ai_confidence` | DECIMAL(3,2) |
| `contains_text` | BOOLEAN DEFAULT false |
| `ocr_text` | TEXT |
| `ocr_confidence` | DECIMAL(3,2) |
| `manual_description` | TEXT |
| `tags` | TEXT[] |
| `file_hash` | VARCHAR(64) |
| `figure_number` | VARCHAR(50) |
| `figure_context` | TEXT |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_content.instructional_videos

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `manufacturer_id` | UUID NOT NULL → krai_core.manufacturers |
| `title` | VARCHAR(255) NOT NULL |
| `description` | TEXT |
| `video_url` | TEXT NOT NULL |
| `thumbnail_url` | TEXT |
| `duration_seconds` | INTEGER |
| `file_size_mb` | INTEGER |
| `video_format` | VARCHAR(20) |
| `resolution` | VARCHAR(20) |
| `language` | VARCHAR(10) DEFAULT 'en' |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_content.links

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `document_id` | UUID NOT NULL → krai_core.documents |
| `url` | TEXT NOT NULL |
| `link_type` | VARCHAR(50) NOT NULL DEFAULT 'external' |
| `page_number` | INTEGER NOT NULL |
| `description` | TEXT |
| `position_data` | JSONB |
| `is_active` | BOOLEAN DEFAULT true |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_content.print_defects

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `manufacturer_id` | UUID NOT NULL → krai_core.manufacturers |
| `product_id` | UUID → krai_core.products |
| `original_image_id` | UUID → krai_content.images |
| `defect_name` | VARCHAR(100) NOT NULL |
| `defect_category` | VARCHAR(50) |
| `defect_description` | TEXT |
| `example_image_url` | TEXT |
| `annotated_image_url` | TEXT |
| `detection_confidence` | DECIMAL(3,2) |
| `common_causes` | JSONB DEFAULT '[]' |
| `recommended_solutions` | JSONB DEFAULT '[]' |
| `related_error_codes` | TEXT[] |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_content.video_products

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `video_id` | UUID NOT NULL → krai_content.videos |
| `product_id` | UUID NOT NULL → krai_core.products |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_content.videos

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `link_id` | UUID → krai_content.links |
| `youtube_id` | VARCHAR(20) |
| `platform` | VARCHAR(20) |
| `video_url` | TEXT |
| `title` | VARCHAR(500) NOT NULL |
| `description` | TEXT |
| `thumbnail_url` | TEXT |
| `duration` | INTEGER |
| `view_count` | BIGINT |
| `like_count` | INTEGER |
| `comment_count` | INTEGER |
| `channel_id` | VARCHAR(50) |
| `channel_title` | VARCHAR(200) |
| `published_at` | TIMESTAMP |
| `manufacturer_id` | UUID → krai_core.manufacturers |
| `series_id` | UUID → krai_core.product_series |
| `document_id` | UUID → krai_core.documents |
| `metadata` | JSONB |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |
| `enriched_at` | TIMESTAMP DEFAULT NOW() |

## krai_core

### krai_core.document_products

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `document_id` | UUID NOT NULL → krai_core.documents |
| `product_id` | UUID NOT NULL → krai_core.products |
| `is_primary_product` | BOOLEAN DEFAULT false |
| `confidence_score` | DECIMAL(3,2) DEFAULT 0.80 |
| `extraction_method` | VARCHAR(50) |
| `page_numbers` | INTEGER[] |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `document_id` | UUID NOT NULL → krai_core.documents |
| `product_id` | UUID NOT NULL → krai_core.products |
| `is_primary_product` | BOOLEAN DEFAULT false |
| `confidence_score` | DECIMAL(3,2) DEFAULT 0.80 |
| `extraction_method` | VARCHAR(50) |
| `page_numbers` | INTEGER[] |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_core.document_relationships

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `primary_document_id` | UUID NOT NULL → krai_core.documents |
| `secondary_document_id` | UUID NOT NULL → krai_core.documents |
| `relationship_type` | VARCHAR(50) NOT NULL |
| `relationship_strength` | DECIMAL(3,2) DEFAULT 0.5 |
| `auto_discovered` | BOOLEAN DEFAULT true |
| `manual_verification` | BOOLEAN DEFAULT false |
| `verification_date` | TIMESTAMP |
| `verified_by` | VARCHAR(100) |
| `notes` | TEXT |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_core.documents

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `manufacturer_id` | UUID → krai_core.manufacturers |
| `product_id` | UUID → krai_core.products |
| `filename` | VARCHAR(255) NOT NULL |
| `original_filename` | VARCHAR(255) |
| `file_size` | BIGINT |
| `file_hash` | VARCHAR(64) |
| `storage_path` | TEXT |
| `storage_url` | TEXT |
| `document_type` | VARCHAR(100) |
| `language` | VARCHAR(10) DEFAULT 'en' |
| `version` | VARCHAR(50) |
| `publish_date` | DATE |
| `page_count` | INTEGER |
| `word_count` | INTEGER |
| `character_count` | INTEGER |
| `content_text` | TEXT |
| `content_summary` | TEXT |
| `extracted_metadata` | JSONB DEFAULT '{}' |
| `processing_status` | VARCHAR(50) DEFAULT 'pending' |
| `confidence_score` | DECIMAL(3,2) |
| `manual_review_required` | BOOLEAN DEFAULT false |
| `manual_review_completed` | BOOLEAN DEFAULT false |
| `manual_review_notes` | TEXT |
| `ocr_confidence` | DECIMAL(3,2) |
| `manufacturer` | VARCHAR(100) |
| `series` | VARCHAR(100) |
| `models` | TEXT[] |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `filename` | VARCHAR(255) NOT NULL |
| `original_filename` | VARCHAR(255) |
| `file_size` | BIGINT |
| `file_hash` | VARCHAR(64) |
| `storage_path` | TEXT |
| `document_type` | VARCHAR(100) |
| `language` | VARCHAR(10) DEFAULT 'en' |
| `version` | VARCHAR(50) |
| `publish_date` | DATE |
| `page_count` | INTEGER |
| `word_count` | INTEGER |
| `character_count` | INTEGER |
| `content_text` | TEXT |
| `content_summary` | TEXT |
| `extracted_metadata` | JSONB DEFAULT '{}' |
| `processing_status` | VARCHAR(50) DEFAULT 'pending' |
| `processing_results` | JSONB DEFAULT NULL |
| `processing_error` | TEXT DEFAULT NULL |
| `confidence_score` | DECIMAL(3,2) |
| `manual_review_completed` | BOOLEAN DEFAULT false |
| `manual_review_notes` | TEXT |
| `ocr_confidence` | DECIMAL(3,2) |
| `manufacturer` | VARCHAR(100) |
| `series` | VARCHAR(100) |
| `models` | TEXT[] |
| `stage_status` | JSONB DEFAULT '{}' |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `filename` | VARCHAR(255) NOT NULL |
| `original_filename` | VARCHAR(255) |
| `file_size` | BIGINT |
| `file_hash` | VARCHAR(64) |
| `storage_path` | TEXT |
| `document_type` | VARCHAR(100) |
| `language` | VARCHAR(10) DEFAULT 'en' |
| `version` | VARCHAR(50) |
| `publish_date` | DATE |
| `page_count` | INTEGER |
| `word_count` | INTEGER |
| `character_count` | INTEGER |
| `content_text` | TEXT |
| `content_summary` | TEXT |
| `extracted_metadata` | JSONB DEFAULT '{}' |
| `processing_status` | VARCHAR(50) DEFAULT 'pending' |
| `processing_results` | JSONB DEFAULT NULL |
| `processing_error` | TEXT DEFAULT NULL |
| `stage_status` | JSONB DEFAULT '{}' |
| `confidence_score` | DECIMAL(3,2) |
| `ocr_confidence` | DECIMAL(3,2) |
| `manual_review_required` | BOOLEAN DEFAULT false |
| `manual_review_completed` | BOOLEAN DEFAULT false |
| `manual_review_notes` | TEXT |
| `manufacturer` | VARCHAR(100) |
| `series` | VARCHAR(100) |
| `models` | TEXT[] |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_core.manufacturers

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `name` | VARCHAR(100) NOT NULL UNIQUE |
| `short_name` | VARCHAR(10) |
| `country` | VARCHAR(50) |
| `founded_year` | INTEGER |
| `website` | VARCHAR(255) |
| `support_email` | VARCHAR(255) |
| `support_phone` | VARCHAR(50) |
| `logo_url` | TEXT |
| `is_competitor` | BOOLEAN DEFAULT false |
| `market_share_percent` | DECIMAL(5,2) |
| `annual_revenue_usd` | BIGINT |
| `employee_count` | INTEGER |
| `headquarters_address` | TEXT |
| `stock_symbol` | VARCHAR(10) |
| `primary_business_segment` | VARCHAR(100) |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_core.oem_relationships

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `brand_manufacturer` | VARCHAR(100) NOT NULL |
| `brand_series_pattern` | VARCHAR(200) NOT NULL |
| `oem_manufacturer` | VARCHAR(100) NOT NULL |
| `relationship_type` | VARCHAR(50) DEFAULT 'engine' |
| `applies_to` | TEXT[] DEFAULT ARRAY['error_codes' |
| `notes` | TEXT |
| `confidence` | FLOAT DEFAULT 1.0 |
| `source` | VARCHAR(100) DEFAULT 'manual' |
| `verified` | BOOLEAN DEFAULT false |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_core.product_accessories

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `product_id` | UUID NOT NULL → krai_core.products |
| `accessory_id` | UUID NOT NULL → krai_core.products |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_core.product_series

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `manufacturer_id` | UUID NOT NULL → krai_core.manufacturers |
| `series_name` | VARCHAR(100) NOT NULL |
| `series_code` | VARCHAR(50) |
| `launch_date` | DATE |
| `end_of_life_date` | DATE |
| `target_market` | VARCHAR(100) |
| `price_range` | VARCHAR(50) |
| `key_features` | JSONB DEFAULT '{}' |
| `series_description` | TEXT |
| `marketing_name` | VARCHAR(150) |
| `successor_series_id` | UUID → krai_core.product_series |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_core.products

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `parent_id` | UUID → krai_core.products |
| `manufacturer_id` | UUID NOT NULL → krai_core.manufacturers |
| `series_id` | UUID → krai_core.product_series |
| `model_number` | VARCHAR(100) NOT NULL |
| `model_name` | VARCHAR(200) |
| `product_type` | VARCHAR(50) NOT NULL DEFAULT 'printer' |
| `launch_date` | DATE |
| `end_of_life_date` | DATE |
| `msrp_usd` | DECIMAL(10,2) |
| `weight_kg` | DECIMAL(8,2) |
| `dimensions_mm` | JSONB |
| `color_options` | TEXT[] |
| `connectivity_options` | TEXT[] |
| `print_technology` | VARCHAR(50) |
| `max_print_speed_ppm` | INTEGER |
| `max_resolution_dpi` | INTEGER |
| `max_paper_size` | VARCHAR(20) |
| `duplex_capable` | BOOLEAN DEFAULT false |
| `network_capable` | BOOLEAN DEFAULT false |
| `mobile_print_support` | BOOLEAN DEFAULT false |
| `supported_languages` | TEXT[] |
| `energy_star_certified` | BOOLEAN DEFAULT false |
| `warranty_months` | INTEGER DEFAULT 12 |
| `service_manual_url` | TEXT |
| `parts_catalog_url` | TEXT |
| `driver_download_url` | TEXT |
| `firmware_version` | VARCHAR(50) |
| `option_dependencies` | JSONB DEFAULT '{}' |
| `replacement_parts` | JSONB DEFAULT '{}' |
| `common_issues` | JSONB DEFAULT '{}' |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

## krai_integrations

### krai_integrations.api_keys

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `service_name` | VARCHAR(100) NOT NULL |
| `api_key_encrypted` | TEXT NOT NULL |
| `is_active` | BOOLEAN DEFAULT true |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_integrations.webhook_logs

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `webhook_url` | TEXT NOT NULL |
| `request_payload` | JSONB |
| `response_status` | INTEGER |
| `response_body` | TEXT |
| `processed_at` | TIMESTAMP DEFAULT NOW() |

## krai_intelligence

### krai_intelligence.chunks

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `document_id` | UUID NOT NULL → krai_core.documents |
| `text_chunk` | TEXT NOT NULL |
| `chunk_index` | INTEGER NOT NULL |
| `page_start` | INTEGER |
| `page_end` | INTEGER |
| `processing_status` | VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending' |
| `fingerprint` | VARCHAR(32) NOT NULL |
| `metadata` | JSONB DEFAULT '{}' |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_intelligence.embeddings

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `chunk_id` | UUID NOT NULL → krai_intelligence.chunks |
| `embedding` | extensions.vector(768) |
| `model_name` | VARCHAR(100) NOT NULL |
| `model_version` | VARCHAR(50) DEFAULT 'latest' |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_intelligence.error_code_images

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT gen_random_uuid() |
| `error_code_id` | UUID NOT NULL → krai_intelligence.error_codes |
| `image_id` | UUID NOT NULL → krai_content.images |
| `match_method` | TEXT |
| `match_confidence` | FLOAT DEFAULT 0.5 |
| `display_order` | INTEGER DEFAULT 0 |
| `created_at` | TIMESTAMPTZ DEFAULT NOW() |

### krai_intelligence.error_code_parts

| Spalte | Typ & Constraints |
|--------|-------------------|
| `error_code_id` | UUID NOT NULL → krai_intelligence.error_codes |
| `part_id` | UUID NOT NULL → krai_parts.parts_catalog |
| `relevance_score` | FLOAT DEFAULT 1.0 |
| `extraction_source` | TEXT |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_intelligence.error_codes

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `chunk_id` | UUID → krai_intelligence.chunks |
| `document_id` | UUID → krai_core.documents |
| `manufacturer_id` | UUID → krai_core.manufacturers |
| `error_code` | VARCHAR(20) NOT NULL |
| `error_description` | TEXT |
| `solution_text` | TEXT |
| `page_number` | INTEGER |
| `confidence_score` | DECIMAL(3,2) |
| `extraction_method` | VARCHAR(50) |
| `requires_technician` | BOOLEAN DEFAULT false |
| `requires_parts` | BOOLEAN DEFAULT false |
| `estimated_fix_time_minutes` | INTEGER |
| `severity_level` | VARCHAR(20) |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_intelligence.product_research_cache

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `manufacturer` | VARCHAR(100) NOT NULL |
| `model_number` | VARCHAR(100) NOT NULL |
| `series_name` | VARCHAR(200) |
| `series_description` | TEXT |
| `specifications` | JSONB DEFAULT '{}'::jsonb |
| `physical_specs` | JSONB DEFAULT '{}'::jsonb |
| `oem_manufacturer` | VARCHAR(100) |
| `oem_relationship_type` | VARCHAR(50) |
| `oem_notes` | TEXT |
| `launch_date` | DATE |
| `eol_date` | DATE |
| `pricing` | JSONB DEFAULT '{}'::jsonb |
| `product_type` | VARCHAR(100) |
| `confidence` | FLOAT DEFAULT 0.0 |
| `source_urls` | TEXT[] |
| `research_date` | TIMESTAMP DEFAULT NOW() |
| `cache_valid_until` | TIMESTAMP |
| `verified` | BOOLEAN DEFAULT false |
| `verified_by` | VARCHAR(100) |
| `verified_at` | TIMESTAMP |
| `notes` | TEXT |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_intelligence.search_analytics

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `search_query` | TEXT NOT NULL |
| `search_type` | VARCHAR(50) |
| `results_count` | INTEGER |
| `click_through_rate` | DECIMAL(5,4) |
| `user_satisfaction_rating` | INTEGER |
| `search_duration_ms` | INTEGER |
| `result_relevance_scores` | JSONB |
| `user_session_id` | VARCHAR(100) |
| `user_id` | UUID |
| `manufacturer_filter` | UUID → krai_core.manufacturers |
| `product_filter` | UUID → krai_core.products |
| `document_type_filter` | VARCHAR(100) |
| `language_filter` | VARCHAR(10) |
| `created_at` | TIMESTAMP DEFAULT NOW() |

## krai_ml

### krai_ml.model_performance_history

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `model_id` | UUID NOT NULL → krai_ml.model_registry |
| `accuracy_score` | DECIMAL(5,4) |
| `precision_score` | DECIMAL(5,4) |
| `recall_score` | DECIMAL(5,4) |
| `f1_score` | DECIMAL(5,4) |
| `evaluated_at` | TIMESTAMP DEFAULT NOW() |

### krai_ml.model_registry

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `model_name` | VARCHAR(100) NOT NULL UNIQUE |
| `model_version` | VARCHAR(50) NOT NULL |
| `model_type` | VARCHAR(50) NOT NULL |
| `framework` | VARCHAR(50) |
| `created_at` | TIMESTAMP DEFAULT NOW() |

## krai_parts

### krai_parts.inventory_levels

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `part_id` | UUID NOT NULL → krai_parts.parts_catalog |
| `warehouse_location` | VARCHAR(100) |
| `current_stock` | INTEGER DEFAULT 0 |
| `minimum_stock_level` | INTEGER DEFAULT 0 |
| `maximum_stock_level` | INTEGER DEFAULT 1000 |
| `last_updated` | TIMESTAMP DEFAULT NOW() |

### krai_parts.parts_catalog

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `manufacturer_id` | UUID NOT NULL → krai_core.manufacturers |
| `part_number` | VARCHAR(100) NOT NULL |
| `part_name` | VARCHAR(255) |
| `part_description` | TEXT |
| `part_category` | VARCHAR(100) |
| `unit_price_usd` | DECIMAL(10,2) |
| `created_at` | TIMESTAMP DEFAULT NOW() |

## krai_service

### krai_service.service_calls

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `manufacturer_id` | UUID NOT NULL → krai_core.manufacturers |
| `product_id` | UUID → krai_core.products |
| `assigned_technician_id` | UUID → krai_service.technicians |
| `call_status` | VARCHAR(50) DEFAULT 'open' |
| `priority_level` | INTEGER DEFAULT 3 |
| `customer_name` | VARCHAR(255) |
| `customer_contact` | TEXT |
| `issue_description` | TEXT |
| `scheduled_date` | TIMESTAMP |
| `completed_date` | TIMESTAMP |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_service.service_history

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `service_call_id` | UUID → krai_service.service_calls |
| `performed_by` | UUID → krai_service.technicians |
| `service_date` | TIMESTAMP DEFAULT NOW() |
| `service_notes` | TEXT |
| `parts_used` | JSONB DEFAULT '[]' |
| `labor_hours` | DECIMAL(4,2) |
| `service_type` | VARCHAR(50) |
| `outcome` | VARCHAR(100) |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

### krai_service.technicians

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `user_id` | UUID |
| `technician_name` | VARCHAR(255) NOT NULL |
| `employee_id` | VARCHAR(50) UNIQUE |
| `email` | VARCHAR(255) |
| `phone` | VARCHAR(50) |
| `certification_level` | VARCHAR(50) |
| `specializations` | TEXT[] |
| `is_active` | BOOLEAN DEFAULT true |
| `hired_date` | DATE |
| `created_at` | TIMESTAMP DEFAULT NOW() |
| `updated_at` | TIMESTAMP DEFAULT NOW() |

## krai_system

### krai_system.audit_log

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `table_name` | VARCHAR(100) NOT NULL |
| `record_id` | UUID NOT NULL |
| `operation` | VARCHAR(10) NOT NULL |
| `old_values` | JSONB |
| `new_values` | JSONB |
| `changed_by` | VARCHAR(100) |
| `changed_at` | TIMESTAMP DEFAULT NOW() |
| `session_id` | VARCHAR(100) |
| `ip_address` | INET |
| `user_agent` | TEXT |

### krai_system.health_checks

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `service_name` | VARCHAR(100) NOT NULL |
| `check_type` | VARCHAR(50) NOT NULL |
| `status` | VARCHAR(20) NOT NULL |
| `response_time_ms` | INTEGER |
| `error_message` | TEXT |
| `details` | JSONB DEFAULT '{}' |
| `checked_at` | TIMESTAMP DEFAULT NOW() |

### krai_system.processing_queue

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `document_id` | UUID → krai_core.documents |
| `chunk_id` | UUID → krai_intelligence.chunks |
| `image_id` | UUID → krai_content.images |
| `video_id` | UUID → krai_content.instructional_videos |
| `task_type` | VARCHAR(50) NOT NULL |
| `priority` | INTEGER DEFAULT 5 |
| `status` | VARCHAR(20) DEFAULT 'pending' |
| `scheduled_at` | TIMESTAMP DEFAULT NOW() |
| `started_at` | TIMESTAMP |
| `completed_at` | TIMESTAMP |
| `error_message` | TEXT |
| `retry_count` | INTEGER DEFAULT 0 |
| `max_retries` | INTEGER DEFAULT 3 |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_system.stage_tracking

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `document_id` | UUID → krai_core.documents |
| `stage_name` | VARCHAR(100) NOT NULL |
| `status` | VARCHAR(50) NOT NULL |
| `started_at` | TIMESTAMPTZ DEFAULT NOW() |
| `completed_at` | TIMESTAMPTZ |
| `error_message` | TEXT |
| `metadata` | JSONB DEFAULT '{}'::jsonb |
| `created_at` | TIMESTAMPTZ DEFAULT NOW() |
| `updated_at` | TIMESTAMPTZ DEFAULT NOW() |

### krai_system.system_metrics

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `metric_name` | VARCHAR(100) NOT NULL |
| `metric_value` | DECIMAL(15,6) |
| `metric_unit` | VARCHAR(20) |
| `metric_category` | VARCHAR(50) |
| `collection_timestamp` | TIMESTAMP DEFAULT NOW() |
| `server_instance` | VARCHAR(100) |
| `additional_context` | JSONB DEFAULT '{}' |

## krai_users

### krai_users.user_sessions

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `user_id` | UUID NOT NULL → krai_users.users |
| `session_token` | VARCHAR(255) NOT NULL |
| `expires_at` | TIMESTAMP NOT NULL |
| `created_at` | TIMESTAMP DEFAULT NOW() |

### krai_users.users

| Spalte | Typ & Constraints |
|--------|-------------------|
| `id` | UUID PRIMARY KEY DEFAULT uuid_generate_v4() |
| `preferred_manufacturer_id` | UUID → krai_core.manufacturers |
| `username` | VARCHAR(100) NOT NULL UNIQUE |
| `email` | VARCHAR(255) NOT NULL UNIQUE |
| `role` | VARCHAR(50) DEFAULT 'user' |
| `created_at` | TIMESTAMP DEFAULT NOW() |

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
- **Tabellen:** 46
- **Migration Files:** 79

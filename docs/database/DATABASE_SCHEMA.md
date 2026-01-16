# KRAI Database Schema Documentation
================================================================================

**Zuletzt aktualisiert:** 23.10.2025 um 13:32 Uhr

**Quelle:** PostgreSQL Database (Production Structure)

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
- [krai_content](#krai-content) (3 Tabellen)

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

- **Schemas:** 3
- **Tabellen:** 9
- **Spalten:** 100

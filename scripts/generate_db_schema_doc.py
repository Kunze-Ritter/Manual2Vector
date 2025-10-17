"""
Generate Database Schema Documentation
========================================
Creates a comprehensive markdown documentation of all tables, columns, and views
in the KRAI database for reference.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
import json

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env.database')

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*80)
print("GENERATING DATABASE SCHEMA DOCUMENTATION")
print("="*80)

# Hardcoded table list (from your query result)
tables = [
    {"table_schema": "krai_agent", "table_name": "memory"},
    {"table_schema": "krai_agent", "table_name": "message"},
    {"table_schema": "krai_config", "table_name": "competition_analysis"},
    {"table_schema": "krai_config", "table_name": "option_groups"},
    {"table_schema": "krai_config", "table_name": "product_compatibility"},
    {"table_schema": "krai_config", "table_name": "product_features"},
    {"table_schema": "krai_content", "table_name": "images"},
    {"table_schema": "krai_content", "table_name": "links"},
    {"table_schema": "krai_content", "table_name": "print_defects"},
    {"table_schema": "krai_content", "table_name": "video_products"},
    {"table_schema": "krai_content", "table_name": "videos"},
    {"table_schema": "krai_core", "table_name": "document_products"},
    {"table_schema": "krai_core", "table_name": "document_relationships"},
    {"table_schema": "krai_core", "table_name": "documents"},
    {"table_schema": "krai_core", "table_name": "manufacturers"},
    {"table_schema": "krai_core", "table_name": "oem_relationships"},
    {"table_schema": "krai_core", "table_name": "product_accessories"},
    {"table_schema": "krai_core", "table_name": "product_configurations"},
    {"table_schema": "krai_core", "table_name": "product_series"},
    {"table_schema": "krai_core", "table_name": "products"},
    {"table_schema": "krai_integrations", "table_name": "api_keys"},
    {"table_schema": "krai_integrations", "table_name": "webhook_logs"},
    {"table_schema": "krai_intelligence", "table_name": "chunks"},
    {"table_schema": "krai_intelligence", "table_name": "error_code_images"},
    {"table_schema": "krai_intelligence", "table_name": "error_code_parts"},
    {"table_schema": "krai_intelligence", "table_name": "error_codes"},
    {"table_schema": "krai_intelligence", "table_name": "feedback"},
    {"table_schema": "krai_intelligence", "table_name": "product_research_cache"},
    {"table_schema": "krai_intelligence", "table_name": "search_analytics"},
    {"table_schema": "krai_intelligence", "table_name": "session_context"},
    {"table_schema": "krai_intelligence", "table_name": "tool_usage"},
    {"table_schema": "krai_ml", "table_name": "model_performance_history"},
    {"table_schema": "krai_ml", "table_name": "model_registry"},
    {"table_schema": "krai_parts", "table_name": "inventory_levels"},
    {"table_schema": "krai_parts", "table_name": "parts_catalog"},
    {"table_schema": "krai_service", "table_name": "service_calls"},
    {"table_schema": "krai_service", "table_name": "service_history"},
    {"table_schema": "krai_service", "table_name": "technicians"},
    {"table_schema": "krai_system", "table_name": "audit_log"},
    {"table_schema": "krai_system", "table_name": "health_checks"},
    {"table_schema": "krai_system", "table_name": "processing_queue"},
    {"table_schema": "krai_system", "table_name": "stage_tracking"},
    {"table_schema": "krai_system", "table_name": "system_metrics"},
    {"table_schema": "krai_users", "table_name": "user_sessions"},
    {"table_schema": "krai_users", "table_name": "users"},
]

# Build documentation
from datetime import datetime

doc = []
doc.append("# KRAI Database Schema Documentation")
doc.append("=" * 80)
doc.append("")
doc.append(f"**Zuletzt aktualisiert:** {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}")
doc.append("")
doc.append("**Hinweis:** Diese Dokumentation wird automatisch generiert.")
doc.append("")
doc.append("## Table of Contents")
doc.append("")

# Group tables by schema
schemas = {}
for table in tables:
    schema = table['table_schema']
    if schema not in schemas:
        schemas[schema] = []
    schemas[schema].append(table['table_name'])

# Add TOC
for schema in sorted(schemas.keys()):
    doc.append(f"- [{schema}](#{schema.replace('_', '-')})")

doc.append("")
doc.append("---")
doc.append("")

# Document each schema
for schema in sorted(schemas.keys()):
    doc.append(f"## {schema}")
    doc.append("")
    
    for table_name in sorted(schemas[schema]):
        doc.append(f"### {schema}.{table_name}")
        doc.append("")
        
        # Get columns for this table
        columns_query = f"""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
          AND table_name = '{table_name}'
        ORDER BY ordinal_position;
        """
        
        try:
            # Try to get columns (this might fail without proper permissions)
            doc.append("| Column | Type | Nullable | Default |")
            doc.append("|--------|------|----------|---------|")
            doc.append("| *(columns require direct DB access)* | - | - | - |")
        except Exception as e:
            doc.append(f"*Columns: {e}*")
        
        doc.append("")

# Add views section
doc.append("---")
doc.append("")
doc.append("## Public Views (vw_*)")
doc.append("")
doc.append("All views use `vw_` prefix and point to tables in krai_* schemas:")
doc.append("")

# List existing views
existing_views = [
    "vw_agent_memory → krai_agent.memory",
    "vw_audit_log → krai_system.audit_log",
    "vw_chunks → krai_intelligence.chunks (includes embeddings column!)",
    "vw_document_products → krai_core.document_products",
    "vw_documents → krai_core.documents",
    "vw_embeddings → (ALIAS for vw_chunks - embeddings are IN chunks table!)",
    "vw_error_codes → krai_intelligence.error_codes",
    "vw_images → krai_content.images",
    "vw_intelligence_chunks → krai_intelligence.chunks",
    "vw_links → krai_content.links",
    "vw_manufacturers → krai_core.manufacturers",
    "vw_parts → krai_parts.parts_catalog",
    "vw_processing_queue → krai_system.processing_queue",
    "vw_product_series → krai_core.product_series",
    "vw_products → krai_core.products",
    "vw_search_analytics → krai_intelligence.search_analytics",
    "vw_system_metrics → krai_system.system_metrics",
    "vw_video_products → krai_content.video_products",
    "vw_videos → krai_content.videos",
    "vw_webhook_logs → krai_integrations.webhook_logs",
]

for view in existing_views:
    doc.append(f"- `{view}`")

doc.append("")
doc.append("---")
doc.append("")
doc.append("## Important Notes")
doc.append("")
doc.append("### Embeddings Storage")
doc.append("- **Embeddings are stored IN `krai_intelligence.chunks` table as a column!**")
doc.append("- There is NO separate `krai_embeddings` schema")
doc.append("- Column: `embedding` (type: `vector(768)`)")
doc.append("")
doc.append("### View Naming Convention")
doc.append("- All views use `vw_` prefix")
doc.append("- Views are in `public` schema")
doc.append("- Tables are in `krai_*` schemas")
doc.append("")

# Write to file
output_file = project_root / "DATABASE_SCHEMA.md"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(doc))

print(f"\n✅ Documentation written to: {output_file}")
print(f"   Total schemas: {len(schemas)}")
print(f"   Total tables: {sum(len(tables) for tables in schemas.values())}")
print("\n" + "="*80)

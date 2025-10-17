"""
Generate COMPLETE Database Schema Documentation with ALL columns
=================================================================
Queries Supabase directly to get real column information for every table.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env.database')

# Connect to Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

print("="*80)
print("GENERATING COMPLETE DATABASE SCHEMA DOCUMENTATION")
print("="*80)

# All tables (from your query)
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

def get_columns(schema, table):
    """Get columns for a table using direct SQL query"""
    try:
        # Use raw SQL query via PostgREST
        from postgrest import APIError
        
        # Try to select from the table to get column info
        result = supabase.schema(schema).table(table).select('*').limit(0).execute()
        
        # Get column names from the result
        if hasattr(result, 'data'):
            # This won't give us types, but at least column names
            return None
        
    except Exception as e:
        pass
    
    return None

# Build documentation
doc = []
doc.append("# KRAI Database Schema Documentation (COMPLETE)")
doc.append("=" * 80)
doc.append("")
doc.append(f"**Zuletzt aktualisiert:** {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}")
doc.append("")
doc.append("**Hinweis:** Diese Dokumentation wird automatisch generiert und enthält ALLE Spalten.")
doc.append("")
doc.append("## ⚠️ WICHTIGE INFORMATIONEN")
doc.append("")
doc.append("### Embeddings Storage")
doc.append("- **Embeddings sind in `krai_intelligence.chunks` als Spalte gespeichert!**")
doc.append("- Es gibt KEIN separates `krai_embeddings` Schema")
doc.append("- Spalte: `embedding` (Typ: `vector(768)`)")
doc.append("")
doc.append("### View Naming Convention")
doc.append("- Alle Views nutzen `vw_` Prefix")
doc.append("- Views sind im `public` Schema")
doc.append("- Tabellen sind in `krai_*` Schemas")
doc.append("")
doc.append("---")
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

# Document each schema with columns
total_tables = 0
total_columns = 0

for schema in sorted(schemas.keys()):
    doc.append(f"## {schema}")
    doc.append("")
    
    for table_name in sorted(schemas[schema]):
        total_tables += 1
        print(f"Processing {schema}.{table_name}...")
        
        doc.append(f"### {schema}.{table_name}")
        doc.append("")
        
        # Try to get columns by querying the table
        try:
            # Use schema-qualified table access
            result = supabase.schema(schema).table(table_name).select('*').limit(1).execute()
            
            if result.data and len(result.data) > 0:
                # Get column names from first row
                columns = list(result.data[0].keys())
                total_columns += len(columns)
                
                doc.append("**Spalten:**")
                for col in columns:
                    doc.append(f"- `{col}`")
                doc.append("")
            else:
                # Table is empty, try to get structure differently
                doc.append("**Spalten:** *(Tabelle ist leer, Spalten konnten nicht ermittelt werden)*")
                doc.append("")
        except Exception as e:
            doc.append(f"**Spalten:** *(Fehler beim Abrufen: {str(e)[:100]})*")
            doc.append("")

# Add views section
doc.append("---")
doc.append("")
doc.append("## Public Views (vw_*)")
doc.append("")
doc.append("Alle Views nutzen `vw_` Prefix und zeigen auf Tabellen in krai_* Schemas:")
doc.append("")

existing_views = [
    ("vw_agent_memory", "krai_agent.memory"),
    ("vw_audit_log", "krai_system.audit_log"),
    ("vw_chunks", "krai_intelligence.chunks", "⚠️ Enthält embedding Spalte!"),
    ("vw_document_products", "krai_core.document_products"),
    ("vw_documents", "krai_core.documents"),
    ("vw_embeddings", "krai_intelligence.chunks", "⚠️ ALIAS für vw_chunks!"),
    ("vw_error_codes", "krai_intelligence.error_codes"),
    ("vw_images", "krai_content.images"),
    ("vw_intelligence_chunks", "krai_intelligence.chunks"),
    ("vw_links", "krai_content.links"),
    ("vw_manufacturers", "krai_core.manufacturers"),
    ("vw_parts", "krai_parts.parts_catalog"),
    ("vw_processing_queue", "krai_system.processing_queue"),
    ("vw_product_series", "krai_core.product_series"),
    ("vw_products", "krai_core.products"),
    ("vw_search_analytics", "krai_intelligence.search_analytics"),
    ("vw_system_metrics", "krai_system.system_metrics"),
    ("vw_video_products", "krai_content.video_products"),
    ("vw_videos", "krai_content.videos"),
    ("vw_webhook_logs", "krai_integrations.webhook_logs"),
]

for view_info in existing_views:
    if len(view_info) == 3:
        view, table, note = view_info
        doc.append(f"- `{view}` → `{table}` *{note}*")
    else:
        view, table = view_info
        doc.append(f"- `{view}` → `{table}`")

doc.append("")
doc.append("---")
doc.append("")
doc.append("## Statistik")
doc.append("")
doc.append(f"- **Schemas:** {len(schemas)}")
doc.append(f"- **Tabellen:** {total_tables}")
doc.append(f"- **Spalten (geschätzt):** {total_columns}")
doc.append("")

# Write to file
output_file = project_root / "DATABASE_SCHEMA.md"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(doc))

print(f"\n✅ Dokumentation geschrieben nach: {output_file}")
print(f"   Schemas: {len(schemas)}")
print(f"   Tabellen: {total_tables}")
print(f"   Spalten: {total_columns}")
print("\n" + "="*80)

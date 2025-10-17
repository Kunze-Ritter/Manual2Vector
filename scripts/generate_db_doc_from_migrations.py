"""
Generate Database Schema Documentation from Migration Files
============================================================
Parses SQL migration files to extract table structures.
"""

import os
import re
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
migrations_dir = project_root / "database" / "migrations"

print("="*80)
print("GENERATING DATABASE SCHEMA DOCUMENTATION FROM MIGRATIONS")
print("="*80)

# Read all migration files
migration_files = sorted(migrations_dir.glob("*.sql"))

# Parse CREATE TABLE statements
tables_info = {}

for migration_file in migration_files:
    print(f"Parsing {migration_file.name}...")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all CREATE TABLE statements
    # Pattern: CREATE TABLE [IF NOT EXISTS] schema.table (columns...)
    pattern = r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([a-z_]+)\.([a-z_]+)\s*\((.*?)\);'
    
    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        schema = match.group(1)
        table = match.group(2)
        columns_text = match.group(3)
        
        # Parse columns
        columns = []
        for line in columns_text.split('\n'):
            line = line.strip()
            if not line or line.startswith('--') or line.startswith('CONSTRAINT') or line.startswith('PRIMARY') or line.startswith('FOREIGN') or line.startswith('UNIQUE') or line.startswith('CHECK'):
                continue
            
            # Extract column name and type
            parts = line.split()
            if len(parts) >= 2:
                col_name = parts[0].strip(',')
                col_type = parts[1].strip(',')
                
                # Build column info
                col_info = f"{col_name} {col_type}"
                
                # Add constraints
                if 'PRIMARY KEY' in line:
                    col_info += " PRIMARY KEY"
                if 'NOT NULL' in line:
                    col_info += " NOT NULL"
                if 'UNIQUE' in line:
                    col_info += " UNIQUE"
                if 'DEFAULT' in line:
                    default_match = re.search(r'DEFAULT\s+([^,\n]+)', line)
                    if default_match:
                        col_info += f" DEFAULT {default_match.group(1).strip()}"
                if 'REFERENCES' in line:
                    ref_match = re.search(r'REFERENCES\s+([a-z_]+\.[a-z_]+)', line)
                    if ref_match:
                        col_info += f" → {ref_match.group(1)}"
                
                columns.append(col_info)
        
        # Store table info
        key = f"{schema}.{table}"
        if key not in tables_info:
            tables_info[key] = columns
        else:
            # Merge columns (in case of ALTER TABLE in later migrations)
            tables_info[key].extend(columns)

print(f"\nFound {len(tables_info)} tables")

# Build documentation
doc = []
doc.append("# KRAI Database Schema Documentation")
doc.append("=" * 80)
doc.append("")
doc.append(f"**Zuletzt aktualisiert:** {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}")
doc.append("")
doc.append("**Quelle:** Generiert aus SQL Migration Files")
doc.append("")
doc.append("## ⚠️ WICHTIGE INFORMATIONEN")
doc.append("")
doc.append("### Embeddings Storage")
doc.append("- **Embeddings sind in `krai_intelligence.chunks` als Spalte `embedding` gespeichert!**")
doc.append("- Es gibt KEIN separates `krai_embeddings` Schema")
doc.append("- Spalte: `embedding` (Typ: `vector(768)`)")
doc.append("")
doc.append("### View Naming Convention")
doc.append("- Alle Views nutzen `vw_` Prefix")
doc.append("- Views sind im `public` Schema")
doc.append("- Tabellen sind in `krai_*` Schemas")
doc.append("")
doc.append("### Wichtige Tabellen für Processing")
doc.append("- `krai_core.documents` - Haupttabelle für Dokumente")
doc.append("- `krai_core.products` - Produkte")
doc.append("- `krai_core.manufacturers` - Hersteller")
doc.append("- `krai_intelligence.chunks` - Text-Chunks mit Embeddings")
doc.append("- `krai_intelligence.error_codes` - Fehlercodes")
doc.append("- `krai_content.videos` - Videos")
doc.append("- `krai_content.links` - Links")
doc.append("- `krai_content.images` - Bilder")
doc.append("- `krai_parts.parts_catalog` - Ersatzteile")
doc.append("")
doc.append("---")
doc.append("")
doc.append("## Table of Contents")
doc.append("")

# Group tables by schema
schemas = {}
for table_key in sorted(tables_info.keys()):
    schema, table = table_key.split('.')
    if schema not in schemas:
        schemas[schema] = []
    schemas[schema].append(table)

# Add TOC
for schema in sorted(schemas.keys()):
    doc.append(f"- [{schema}](#{schema.replace('_', '-')}) ({len(schemas[schema])} Tabellen)")

doc.append("")
doc.append("---")
doc.append("")

# Document each schema
for schema in sorted(schemas.keys()):
    doc.append(f"## {schema}")
    doc.append("")
    
    for table in sorted(schemas[schema]):
        table_key = f"{schema}.{table}"
        doc.append(f"### {table_key}")
        doc.append("")
        
        if table_key in tables_info and tables_info[table_key]:
            doc.append("| Spalte | Typ & Constraints |")
            doc.append("|--------|-------------------|")
            
            for col_info in tables_info[table_key]:
                parts = col_info.split(' ', 1)
                col_name = parts[0]
                col_rest = parts[1] if len(parts) > 1 else ""
                doc.append(f"| `{col_name}` | {col_rest} |")
            
            doc.append("")
        else:
            doc.append("*Keine Spalten gefunden*")
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
    ("vw_embeddings", "ALIAS für vw_chunks", "⚠️ Embeddings sind IN chunks!"),
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

doc.append("| View | Zeigt auf | Hinweis |")
doc.append("|------|-----------|---------|")

for view_info in existing_views:
    if len(view_info) == 3:
        view, table, note = view_info
        doc.append(f"| `{view}` | `{table}` | {note} |")
    else:
        view, table = view_info
        doc.append(f"| `{view}` | `{table}` | - |")

doc.append("")
doc.append("---")
doc.append("")
doc.append("## Statistik")
doc.append("")
doc.append(f"- **Schemas:** {len(schemas)}")
doc.append(f"- **Tabellen:** {len(tables_info)}")
doc.append(f"- **Migration Files:** {len(migration_files)}")
doc.append("")

# Write to file
output_file = project_root / "DATABASE_SCHEMA.md"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(doc))

print(f"\n✅ Dokumentation geschrieben nach: {output_file}")
print(f"   Schemas: {len(schemas)}")
print(f"   Tabellen: {len(tables_info)}")
print("\n" + "="*80)

"""
Reload PostgREST Schema Cache

This script forces PostgREST to reload its schema cache.
Run this after adding/modifying database columns.
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database connection URL
db_url = os.getenv('DATABASE_CONNECTION_URL')

if not db_url:
    print("❌ DATABASE_CONNECTION_URL not found in .env")
    exit(1)

try:
    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Send NOTIFY to reload PostgREST schema
    print("📢 Sending NOTIFY to PostgREST...")
    cursor.execute("NOTIFY pgrst, 'reload schema';")
    
    print("✅ PostgREST schema cache reload signal sent!")
    print("   PostgREST should reload its schema within a few seconds.")
    
    # Close connection
    cursor.close()
    conn.close()
    
    print("\n✅ Done! The manufacturer_id column should now be accessible.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

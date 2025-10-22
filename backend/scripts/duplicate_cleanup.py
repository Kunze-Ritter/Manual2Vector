#!/usr/bin/env python3
"""
Duplicate Cleanup Script for KR-AI-Engine
Safely merges and removes duplicate documents while preserving data integrity
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from backend.services.database_service_production import DatabaseService

class DuplicateCleanup:
    def __init__(self):
        self.database_service = None
        
    async def initialize(self):
        """Initialize database service"""
        print("🔧 Initializing Duplicate Cleanup Service...")
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize database service
        self.database_service = DatabaseService(
            supabase_url=os.getenv('SUPABASE_URL'),
            supabase_key=os.getenv('SUPABASE_ANON_KEY')
        )
        await self.database_service.connect()
        
        print("✅ Service initialized")
    
    async def analyze_duplicates(self):
        """Analyze all duplicates in the database"""
        print("\n🔍 ANALYZING DUPLICATES...")
        
        # Get document duplicates
        doc_duplicates = await self.database_service.client.rpc('get_document_duplicates').execute()
        
        if not doc_duplicates.data:
            print("✅ No document duplicates found!")
            return {}
        
        print(f"📊 Found {len(doc_duplicates.data)} duplicate groups")
        
        # Group by hash
        duplicate_groups = {}
        for dup in doc_duplicates.data:
            file_hash = dup['file_hash']
            if file_hash not in duplicate_groups:
                duplicate_groups[file_hash] = []
            duplicate_groups[file_hash].append(dup)
        
        return duplicate_groups
    
    async def merge_duplicate_group(self, file_hash: str, documents: List[Dict[str, Any]]):
        """Merge a group of duplicate documents"""
        print(f"\n🔧 Merging {len(documents)} duplicates for hash {file_hash[:16]}...")
        
        # Sort by creation date (keep the oldest as master)
        documents.sort(key=lambda x: x['created_at'])
        master_doc = documents[0]
        duplicates = documents[1:]
        
        print(f"  📋 Master: {master_doc['filename']} (ID: {master_doc['id'][:8]}...)")
        print(f"  🗑️  Removing {len(duplicates)} duplicates...")
        
        # Get all related data for master document
        master_id = master_doc['id']
        
        # Count related data
        chunks_count = await self.count_related_chunks(master_id)
        images_count = await self.count_related_images(master_id)
        
        print(f"  📄 Master has {chunks_count} chunks, {images_count} images")
        
        # For each duplicate, check if it has more data than master
        for dup in duplicates:
            dup_id = dup['id']
            dup_chunks = await self.count_related_chunks(dup_id)
            dup_images = await self.count_related_images(dup_id)
            
            print(f"  📄 Duplicate {dup['filename']} has {dup_chunks} chunks, {dup_images} images")
            
            # If duplicate has more data, merge it into master
            if dup_chunks > chunks_count or dup_images > images_count:
                print(f"  🔄 Merging duplicate data into master...")
                await self.merge_document_data(master_id, dup_id)
                chunks_count = max(chunks_count, dup_chunks)
                images_count = max(images_count, dup_images)
        
        # Delete all duplicates
        duplicate_ids = [dup['id'] for dup in duplicates]
        await self.delete_documents(duplicate_ids)
        
        print(f"  ✅ Merged and cleaned {len(duplicates)} duplicates")
        return len(duplicates)
    
    async def count_related_chunks(self, document_id: str) -> int:
        """Count chunks related to a document"""
        try:
            result = self.database_service.client.table('vw_chunks').select('id', count='exact').eq('document_id', document_id).execute()
            return result.count if result.count else 0
        except:
            return 0
    
    async def count_related_images(self, document_id: str) -> int:
        """Count images related to a document"""
        try:
            result = self.database_service.client.table('vw_images').select('id', count='exact').eq('document_id', document_id).execute()
            return result.count if result.count else 0
        except:
            return 0
    
    async def merge_document_data(self, master_id: str, duplicate_id: str):
        """Merge data from duplicate into master document"""
        try:
            # Update chunks to point to master document
            await self.database_service.client.table('vw_chunks').update({'document_id': master_id}).eq('document_id', duplicate_id).execute()
            
            # Update images to point to master document
            await self.database_service.client.table('vw_images').update({'document_id': master_id}).eq('document_id', duplicate_id).execute()
            
            print(f"    📄 Merged chunks and images from {duplicate_id[:8]}... to {master_id[:8]}...")
            
        except Exception as e:
            print(f"    ❌ Failed to merge data: {e}")
    
    async def delete_documents(self, document_ids: List[str]):
        """Delete duplicate documents (cascading will handle related data)"""
        try:
            # Delete documents (cascading will handle chunks/images)
            for doc_id in document_ids:
                await self.database_service.client.table('vw_documents').delete().eq('id', doc_id).execute()
            
            print(f"    🗑️  Deleted {len(document_ids)} duplicate documents")
            
        except Exception as e:
            print(f"    ❌ Failed to delete documents: {e}")
    
    async def run_cleanup(self):
        """Run the complete duplicate cleanup process"""
        print("🚀 Starting Duplicate Cleanup Process...")
        
        # Analyze duplicates
        duplicate_groups = await self.analyze_duplicates()
        
        if not duplicate_groups:
            print("✅ No duplicates found - database is clean!")
            return
        
        total_duplicates_removed = 0
        
        # Process each duplicate group
        for file_hash, documents in duplicate_groups.items():
            duplicates_removed = await self.merge_duplicate_group(file_hash, documents)
            total_duplicates_removed += duplicates_removed
        
        print(f"\n🎉 CLEANUP COMPLETE!")
        print(f"  📊 Total duplicates removed: {total_duplicates_removed}")
        print(f"  📁 Duplicate groups processed: {len(duplicate_groups)}")
        
        # Final verification
        remaining_duplicates = await self.analyze_duplicates()
        if remaining_duplicates:
            print(f"  ⚠️  {len(remaining_duplicates)} duplicate groups still remain")
        else:
            print(f"  ✅ Database is now completely clean!")

async def main():
    cleanup = DuplicateCleanup()
    await cleanup.initialize()
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will permanently delete duplicate documents!")
    print("   Only the oldest document in each duplicate group will be kept.")
    print("   All data will be merged into the master document.")
    
    confirm = input("\nProceed with cleanup? (yes/no): ").lower().strip()
    
    if confirm in ['yes', 'y']:
        await cleanup.run_cleanup()
    else:
        print("❌ Cleanup cancelled by user")

if __name__ == "__main__":
    asyncio.run(main())

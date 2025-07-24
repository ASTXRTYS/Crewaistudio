#!/usr/bin/env python3
"""
Neuroscientist Knowledge Injection Verification Script
Comprehensive verification that all neuroscientist knowledge files were properly injected
"""

import asyncio
import sqlite3
import json
import os
from pathlib import Path
import aiosqlite

class NeuroscientistKnowledgeVerifier:
    """Verifies complete neuroscientist knowledge injection"""
    
    def __init__(self):
        self.db_path = "auren_knowledge.db"
        self.knowledge_folder = Path("./src/agents/Level 1 knowledge ")
        
    async def verify_folder_structure(self):
        """Verify the knowledge folder structure and files"""
        
        print("🔍 VERIFYING LEVEL 1 KNOWLEDGE FOLDER STRUCTURE")
        print("=" * 60)
        
        # Check if folder exists
        if not self.knowledge_folder.exists():
            print(f"❌ Knowledge folder not found: {self.knowledge_folder}")
            # Try alternative paths
            alt_paths = [
                "./src/agents/Level 1 knowledge",
                "src/agents/Level 1 knowledge ",
                "src/agents/Level 1 knowledge/"
            ]
            for alt_path in alt_paths:
                if Path(alt_path).exists():
                    self.knowledge_folder = Path(alt_path)
                    print(f"✅ Found folder: {alt_path}")
                    break
            else:
                print("❌ Could not locate knowledge folder")
                return False
        
        # List all files in the folder
        all_files = list(self.knowledge_folder.glob("*.md"))
        neuroscientist_files = [f for f in all_files if f.name.startswith("neuroscientist_")]
        
        print(f"📁 Knowledge folder: {self.knowledge_folder}")
        print(f"📊 Total .md files: {len(all_files)}")
        print(f"🧠 Neuroscientist files: {len(neuroscientist_files)}")
        
        # List all files with details
        print("\n📋 ALL FILES IN LEVEL 1 KNOWLEDGE:")
        for file in sorted(all_files):
            specialist_type = "NEUROSCIENTIST" if file.name.startswith("neuroscientist_") else "OTHER"
            print(f"   {specialist_type}: {file.name}")
        
        return neuroscientist_files
    
    async def verify_database_injection(self, expected_files):
        """Verify all neuroscientist files were injected into database"""
        
        print("\n🔍 VERIFYING DATABASE INJECTION")
        print("=" * 60)
        
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return False
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get all neuroscientist knowledge from database
            async with db.execute("""
                SELECT knowledge_type, title, source_file 
                FROM neuroscientist_knowledge 
                ORDER BY knowledge_type
            """) as cursor:
                db_knowledge = await cursor.fetchall()
            
            # Get all neuroscientist agent memories
            async with db.execute("""
                SELECT agent_id, memory_type, content 
                FROM agent_memories 
                WHERE agent_id = 'neuroscientist'
                ORDER BY created_at
            """) as cursor:
                db_memories = await cursor.fetchall()
            
            print(f"📊 Database records:")
            print(f"   ✅ neuroscientist_knowledge table: {len(db_knowledge)} items")
            print(f"   ✅ agent_memories table: {len(db_memories)} items")
            
            # Map expected files to database records
            expected_knowledge_types = [f.stem.replace('neuroscientist_', '') for f in expected_files]
            actual_knowledge_types = [row[0] for row in db_knowledge]
            
            print(f"\n📋 INJECTION VERIFICATION:")
            
            # Check each expected file
            all_injected = True
            for expected_file in expected_files:
                knowledge_type = expected_file.stem.replace('neuroscientist_', '')
                
                if knowledge_type in actual_knowledge_types:
                    print(f"   ✅ {expected_file.name}")
                else:
                    print(f"   ❌ {expected_file.name} - NOT INJECTED")
                    all_injected = False
            
            # Show database entries
            print(f"\n🗄️ DATABASE ENTRIES:")
            for knowledge_type, title, source_file in db_knowledge:
                print(f"   📋 {knowledge_type} -> {title}")
            
            return all_injected
    
    async def verify_content_integrity(self, expected_files):
        """Verify content integrity by checking file sizes and basic content"""
        
        print("\n🔍 VERIFYING CONTENT INTEGRITY")
        print("=" * 60)
        
        integrity_issues = []
        
        for file_path in expected_files:
            try:
                # Read original file
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Check database content
                knowledge_type = file_path.stem.replace('neuroscientist_', '')
                
                async with aiosqlite.connect(self.db_path) as db:
                    async with db.execute("""
                        SELECT content FROM neuroscientist_knowledge 
                        WHERE knowledge_type = ?
                    """, (knowledge_type,)) as cursor:
                        db_content = await cursor.fetchone()
                
                if db_content:
                    # Basic integrity check - compare lengths
                    original_length = len(original_content)
                    db_length = len(db_content[0])
                    
                    if abs(original_length - db_length) > 100:  # Allow small differences
                        integrity_issues.append(f"{file_path.name}: Size mismatch {original_length} vs {db_length}")
                    else:
                        print(f"   ✅ {file_path.name}: Content integrity verified")
                else:
                    integrity_issues.append(f"{file_path.name}: No content in database")
                    
            except Exception as e:
                integrity_issues.append(f"{file_path.name}: Error - {str(e)}")
        
        if integrity_issues:
            print("\n⚠️ INTEGRITY ISSUES:")
            for issue in integrity_issues:
                print(f"   ❌ {issue}")
        
        return len(integrity_issues) == 0
    
    async def run_complete_verification(self):
        """Run complete verification process"""
        
        print("🧠 NEUROSCIENTIST KNOWLEDGE INJECTION VERIFICATION")
        print("=" * 80)
        
        # Step 1: Verify folder structure
        neuroscientist_files = await self.verify_folder_structure()
        if not neuroscientist_files:
            print("❌ Cannot proceed - no neuroscientist files found")
            return False
        
        # Step 2: Verify database injection
        injection_complete = await self.verify_database_injection(neuroscientist_files)
        
        # Step 3: Verify content integrity
        integrity_ok = await self.verify_content_integrity(neuroscientist_files)
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎯 VERIFICATION SUMMARY")
        print("=" * 80)
        
        if injection_complete and integrity_ok:
            print("🎉 ALL NEUROSCIENTIST KNOWLEDGE SUCCESSFULLY INJECTED")
            print(f"   ✅ {len(neuroscientist_files)} neuroscientist files")
            print("   ✅ All content integrity verified")
            print("   ✅ Database injection complete")
            return True
        else:
            print("❌ INJECTION INCOMPLETE")
            if not injection_complete:
                print("   ❌ Some files not injected")
            if not integrity_ok:
                print("   ❌ Content integrity issues")
            return False

async def main():
    """Main verification execution"""
    verifier = NeuroscientistKnowledgeVerifier()
    success = await verifier.run_complete_verification()
    
    if success:
        print("\n🚀 Ready for neuroscientist agent activation!")
    else:
        print("\n🔧 Please fix the issues above before proceeding")

if __name__ == "__main__":
    asyncio.run(main())

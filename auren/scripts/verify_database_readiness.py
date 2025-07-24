#!/usr/bin/env python3
"""
Database Readiness Verification for Knowledge Injection
Validates PostgreSQL is ready for clinical knowledge loading
"""

import asyncio
import asyncpg
import os
from datetime import datetime

async def verify_database_readiness():
    """
    Comprehensive verification that PostgreSQL is ready for knowledge injection
    """
    
    print("🔍 VERIFYING DATABASE READINESS FOR KNOWLEDGE INJECTION")
    print("=" * 60)
    
    # Database connection configuration
    dsn = os.getenv('AUREN_DSN', 'postgresql://auren_user:password@localhost:5432/auren')
    
    try:
        # Connect to database
        conn = await asyncpg.connect(dsn)
        print(f"✅ Connected to database: {dsn}")
        
        # Test 1: Verify required tables exist
        tables_check = await verify_required_tables(conn)
        
        # Test 2: Verify schema is correct
        schema_check = await verify_schema_structure(conn)
        
        # Test 3: Test basic operations
        operations_check = await test_basic_operations(conn)
        
        # Test 4: Check for existing knowledge data
        existing_data_check = await check_existing_knowledge(conn)
        
        # Test 5: Verify performance targets
        performance_check = await test_performance_targets(conn)
        
        await conn.close()
        
        all_checks = [tables_check, schema_check, operations_check, existing_data_check, performance_check]
        all_passed = all(check["status"] == "PASSED" for check in all_checks)
        
        print(f"\n🎯 DATABASE READINESS: {'✅ READY' if all_passed else '❌ NOT READY'}")
        
        if not all_passed:
            print("\n🔧 Required fixes:")
            for check in all_checks:
                if check["status"] != "PASSED":
                    print(f"   - {check['name']}: {check.get('fix_instruction', 'See details above')}")
        
        return {
            "database_ready": all_passed,
            "checks": {check["name"]: check for check in all_checks},
            "dsn": dsn
        }
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return {"database_ready": False, "error": str(e)}

async def verify_required_tables(conn):
    """Verify all required tables exist"""
    
    required_tables = [
        'agent_memories', 
        'events', 
        'global_patterns', 
        'clinical_consultations',
        'hypothesis_validation',
        'data_access_audit'
    ]
    
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = ANY($1)
    """
    
    existing_tables = await conn.fetch(query, required_tables)
    existing_table_names = [row['table_name'] for row in existing_tables]
    
    missing_tables = [table for table in required_tables if table not in existing_table_names]
    
    status = "PASSED" if not missing_tables else "FAILED"
    
    print(f"📋 Required Tables Check: {status}")
    for table in required_tables:
        symbol = "✅" if table in existing_table_names else "❌"
        print(f"   {symbol} {table}")
    
    return {
        "name": "required_tables",
        "status": status,
        "existing_tables": existing_table_names,
        "missing_tables": missing_tables,
        "fix_instruction": f"Run database schema creation for: {missing_tables}" if missing_tables else None
    }

async def verify_schema_structure(conn):
    """Verify table schemas are correct for knowledge injection"""
    
    # Check agent_memories table structure
    query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'agent_memories'
    ORDER BY ordinal_position
    """
    
    columns = await conn.fetch(query)
    column_info = {row['column_name']: row['data_type'] for row in columns}
    
    required_columns = {
        'id': 'integer',
        'agent_id': 'character varying',
        'user_id': 'character varying', 
        'memory_type': 'character varying',
        'content': 'jsonb',
        'confidence_score': 'double precision',
        'created_at': 'timestamp with time zone'
    }
    
    missing_columns = []
    wrong_types = []
    
    for col_name, expected_type in required_columns.items():
        if col_name not in column_info:
            missing_columns.append(col_name)
        elif expected_type not in column_info[col_name]:
            wrong_types.append(f"{col_name} (expected {expected_type}, got {column_info[col_name]})")
    
    status = "PASSED" if not missing_columns and not wrong_types else "FAILED"
    
    print(f"🏗️ Schema Structure Check: {status}")
    if missing_columns:
        print(f"   ❌ Missing columns: {missing_columns}")
    if wrong_types:
        print(f"   ❌ Wrong types: {wrong_types}")
    if status == "PASSED":
        print(f"   ✅ All required columns present with correct types")
    
    return {
        "name": "schema_structure",
        "status": status,
        "missing_columns": missing_columns,
        "wrong_types": wrong_types,
        "fix_instruction": "Run schema migration to add missing columns" if missing_columns or wrong_types else None
    }

async def test_basic_operations(conn):
    """Test basic database operations for knowledge injection"""
    
    try:
        # Test insert
        test_id = await conn.fetchval("""
        INSERT INTO agent_memories (agent_id, user_id, memory_type, content, confidence_score)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """, "test_agent", "test_user", "test_knowledge", 
            {"test": "verification"}, 0.8)
        
        # Test retrieve
        retrieved = await conn.fetchrow("""
        SELECT * FROM agent_memories WHERE id = $1
        """, test_id)
        
        # Test update
        await conn.execute("""
        UPDATE agent_memories SET confidence_score = $1 WHERE id = $2
        """, 0.9, test_id)
        
        # Test delete (cleanup)
        await conn.execute("""
        DELETE FROM agent_memories WHERE id = $1
        """, test_id)
        
        print(f"🔧 Basic Operations Check: PASSED")
        print(f"   ✅ Insert, select, update, delete all working")
        
        return {
            "name": "basic_operations",
            "status": "PASSED"
        }
        
    except Exception as e:
        print(f"🔧 Basic Operations Check: FAILED")
        print(f"   ❌ Error: {e}")
        
        return {
            "name": "basic_operations",
            "status": "FAILED",
            "error": str(e),
            "fix_instruction": "Check database permissions and table structure"
        }

async def check_existing_knowledge(conn):
    """Check for any existing knowledge data"""
    
    # Check for existing neuroscientist knowledge
    existing_knowledge = await conn.fetchval("""
    SELECT COUNT(*) FROM agent_memories 
    WHERE agent_id = 'neuroscientist' 
    AND memory_type = 'clinical_knowledge'
    """)
    
    # Check for any system knowledge
    system_knowledge = await conn.fetchval("""
    SELECT COUNT(*) FROM agent_memories 
    WHERE user_id = 'system'
    """)
    
    print(f"📊 Existing Knowledge Check:")
    print(f"   📋 Neuroscientist knowledge items: {existing_knowledge}")
    print(f"   📋 Total system knowledge items: {system_knowledge}")
    
    recommendation = "CLEAN_SLATE" if existing_knowledge == 0 else "APPEND_OR_REPLACE"
    
    return {
        "name": "existing_knowledge",
        "status": "INFO",
        "neuroscientist_knowledge_count": existing_knowledge,
        "system_knowledge_count": system_knowledge,
        "recommendation": recommendation
    }

async def test_performance_targets(conn):
    """Test performance targets for knowledge injection"""
    
    # Create test data
    test_data = [
        ("neuroscientist", "system", "clinical_knowledge", {"test": "performance"}, 0.8)
        for _ in range(1000)
    ]
    
    start_time = datetime.now()
    
    # Batch insert
    await conn.executemany("""
    INSERT INTO agent_memories (agent_id, user_id, memory_type, content, confidence_score)
    VALUES ($1, $2, $3, $4, $5)
    """, test_data)
    
    insert_time = (datetime.now() - start_time).total_seconds()
    
    # Test retrieval
    start_time = datetime.now()
    retrieved = await conn.fetch("""
    SELECT * FROM agent_memories WHERE agent_id = 'neuroscientist' LIMIT 100
    """)
    retrieve_time = (datetime.now() - start_time).total_seconds()
    
    # Cleanup
    await conn.execute("""
    DELETE FROM agent_memories WHERE agent_id = 'neuroscientist' AND user_id = 'system'
    """)
    
    print(f"⚡ Performance Check:")
    print(f"   ✅ Batch insert 1000 items: {insert_time:.3f}s")
    print(f"   ✅ Retrieve 100 items: {retrieve_time:.3f}s")
    
    targets_met = insert_time < 1.0 and retrieve_time < 0.1
    
    return {
        "name": "performance_targets",
        "status": "PASSED" if targets_met else "WARNING",
        "insert_time": insert_time,
        "retrieve_time": retrieve_time,
        "targets_met": targets_met
    }

async def main():
    """Main execution function"""
    result = await verify_database_readiness()
    
    if result["database_ready"]:
        print("\n🎉 DATABASE IS READY FOR KNOWLEDGE INJECTION!")
        print("Proceed with knowledge injection using:")
        print(f"   DSN: {result['dsn']}")
    else:
        print("\n❌ DATABASE NEEDS ATTENTION")
        print("Please fix the issues above before proceeding")

if __name__ == "__main__":
    asyncio.run(main())

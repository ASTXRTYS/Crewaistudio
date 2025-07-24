# 🚀 Execute Knowledge Loading - Quick Guide

## One-Line Setup (macOS)

```bash
./auren/scripts/setup_postgres.sh && pip install -r auren/requirements.txt && python auren/scripts/test_database_connection.py && python auren/scripts/load_knowledge_base.py
```

## Step-by-Step Execution

### 1. Setup PostgreSQL (2 minutes)
```bash
./auren/scripts/setup_postgres.sh
```

### 2. Install Dependencies (1 minute)
```bash
pip install -r auren/requirements.txt
```

### 3. Test Database Connection (10 seconds)
```bash
python auren/scripts/test_database_connection.py
```

Expected output:
```
Testing PostgreSQL connection...
✅ Database connection successful
✅ Database schema initialized
Current knowledge items in database: 0
```

### 4. Load Knowledge Base (2 minutes)
```bash
python auren/scripts/load_knowledge_base.py
```

Expected output:
```
🚀 Starting knowledge base loading...
Found 15 knowledge files to load

📄 Loading: CNS relevant training .md
✅ Loaded 'CNS Relevant Training' to neuroscience domain (confidence: 0.85)

[... 13 more files ...]

📄 Loading: neuroscientist_visual_fatigue_protocols.md
✅ Loaded 'Visual Fatigue Protocols' to neuroscience domain (confidence: 0.88)

📊 Loading Summary:
Total files: 15
Successfully loaded: 15
Failed: 0

Neuroscientist knowledge base: 15 knowledge items
(All knowledge belongs to the single Neuroscientist agent)

✅ Knowledge base loading complete!
```

## Total Time: ~5 minutes

## What Happens Next?

The Neuroscientist agent now has access to all 15 knowledge items covering:
- CNS optimization
- HRV analytics  
- Sleep recovery correlations
- Stress assessment protocols
- Movement optimization
- Metabolic optimization
- Emergency response protocols
- And more...

All knowledge is properly stored in PostgreSQL with full event sourcing and can be accessed via the KnowledgeManager.

## Troubleshooting

If you encounter any issues:
1. Check PostgreSQL is running: `brew services list`
2. Check logs: `tail -f /opt/homebrew/var/log/postgresql@14.log`
3. Verify database exists: `psql -l | grep auren`
4. Check Python dependencies: `pip list | grep asyncpg`

## Architecture Note

Remember: All 15 files belong to ONE agent - the Neuroscientist. They represent different aspects of expertise, not different agents. 
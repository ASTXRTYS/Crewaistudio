# AUREN Knowledge Base Loading

## Important Architecture Note

**For the MVP, there is only ONE agent: the Neuroscientist**

The 15 knowledge files with different specialist names are all aspects of the SAME Neuroscientist agent:
- CNS Optimization Specialist = Neuroscientist
- Health Orchestration Coordinator = Neuroscientist  
- Metabolic Optimization Specialist = Neuroscientist
- Movement Optimization Specialist = Neuroscientist
- All neuroscientist_*.md files = Neuroscientist

They represent different areas of expertise within the single Neuroscientist agent.

## Prerequisites

1. PostgreSQL installed and running
2. Python environment with dependencies installed
3. AUREN database created

## Setup Steps

### Quick Setup (macOS)

```bash
# Run the automated setup script
./auren/scripts/setup_postgres.sh
```

This script will:
- Install PostgreSQL via Homebrew (if needed)
- Start the PostgreSQL service
- Create the 'auren' database
- Test the connection

### Manual Setup

#### 1. Install PostgreSQL (if not already installed)

```bash
# macOS
brew install postgresql
brew services start postgresql

# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### 2. Create the AUREN database

```bash
createdb auren
```

### 3. Configure Database Connection (Optional)

The system uses these environment variables (with defaults):
- `DATABASE_URL` (default: `postgresql://localhost:5432/auren`)
- `DATABASE_MIN_CONNECTIONS` (default: `1`)
- `DATABASE_MAX_CONNECTIONS` (default: `10`)

If using non-default PostgreSQL settings, export the DATABASE_URL:
```bash
export DATABASE_URL=postgresql://user:password@host:port/dbname
```

### 4. Install Python dependencies

```bash
# From the project root (AUREN-Studio-main)
pip install -r auren/requirements.txt
```

## Running the Knowledge Loader

### Step 1: Test Database Connection

```bash
# From the project root (AUREN-Studio-main)
python auren/scripts/test_database_connection.py
```

This will verify:
- PostgreSQL is accessible
- Database schema is created
- Connection parameters are correct

### Step 2: Load Knowledge Base

```bash
# From the project root (AUREN-Studio-main)
python auren/scripts/load_knowledge_base.py
```

This will:
1. Parse all 15 markdown files from `auren/src/agents/Level 1 knowledge/`
2. Create KnowledgeItem objects for each file
3. Load all knowledge into the Neuroscientist's knowledge base
4. Maintain event sourcing via EventStore
5. Display loading statistics

## Expected Output

```
🚀 Starting knowledge base loading...
Found 15 knowledge files to load

📄 Loading: CNS relevant training .md
✅ Loaded 'CNS Relevant Training' to neuroscience domain (confidence: 0.85)

📄 Loading: neuroscientist_hrv_analytics.md
✅ Loaded 'HRV Analytics Protocol' to neuroscience domain (confidence: 0.92)

[... continues for all 15 files ...]

📊 Loading Summary:
Total files: 15
Successfully loaded: 15
Failed: 0

Neuroscientist knowledge base: 15 knowledge items
(All knowledge belongs to the single Neuroscientist agent)

✅ Knowledge base loading complete!
```

## Troubleshooting

### Database Connection Errors

If you see connection errors:

1. Check PostgreSQL is running:
   ```bash
   psql -U postgres -c "SELECT 1"
   ```

2. Check the connection string in `data_layer/connection.py`:
   ```python
   database_url: str = "postgresql://localhost:5432/auren"
   ```

3. If using custom PostgreSQL settings, update the connection string

### Import Errors

If you see import errors:
1. Ensure you're running from the correct directory
2. Check that all Module A & B files are present
3. Verify Python path includes the auren directory

### Knowledge Loading Errors

If specific files fail to load:
1. Check the markdown file syntax
2. Verify the ClinicalMarkdownParser can handle the format
3. Check logs for specific parsing errors

## Architecture Compliance

This loader maintains full compliance with Modules A & B:

✅ Uses `ClinicalMarkdownParser` from Module B  
✅ Creates proper `KnowledgeItem` objects  
✅ Uses `KnowledgeManager.add_knowledge()` method  
✅ Maintains event sourcing via `EventStore`  
✅ Stores in PostgreSQL via `PostgreSQLMemoryBackend`  
✅ No direct database inserts  
✅ All architectural patterns preserved  

## Next Steps

After loading the knowledge base:

1. The Neuroscientist agent can access all 15 knowledge items
2. Knowledge retrieval works through the KnowledgeManager
3. The agent can use this knowledge for HRV analysis, CNS assessment, etc.
4. Event history is maintained for audit trails 
#!/bin/bash
# PostgreSQL Setup Script for AUREN Knowledge Loading

echo "🚀 AUREN PostgreSQL Setup Script"
echo "================================"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "📦 PostgreSQL not found. Installing via Homebrew..."
    brew install postgresql
    
    # Start PostgreSQL service
    echo "🔧 Starting PostgreSQL service..."
    brew services start postgresql
    
    # Wait for PostgreSQL to start
    echo "⏳ Waiting for PostgreSQL to start..."
    sleep 5
else
    echo "✅ PostgreSQL is already installed"
    
    # Check if PostgreSQL is running
    if ! pg_isready &> /dev/null; then
        echo "🔧 PostgreSQL is not running. Starting it..."
        brew services start postgresql
        sleep 5
    else
        echo "✅ PostgreSQL is running"
    fi
fi

# Create the AUREN database
echo ""
echo "📊 Creating AUREN database..."
if createdb auren 2>/dev/null; then
    echo "✅ Database 'auren' created successfully"
else
    echo "ℹ️  Database 'auren' already exists (this is fine)"
fi

# Test the connection
echo ""
echo "🔍 Testing database connection..."
if psql -d auren -c "SELECT 1;" &> /dev/null; then
    echo "✅ Database connection successful!"
else
    echo "❌ Database connection failed"
    echo "Please check PostgreSQL logs: brew services info postgresql"
    exit 1
fi

echo ""
echo "🎉 PostgreSQL setup complete!"
echo ""
echo "Next steps:"
echo "1. Install Python dependencies: pip install -r auren/requirements.txt"
echo "2. Test connection: python auren/scripts/test_database_connection.py"
echo "3. Load knowledge: python auren/scripts/load_knowledge_base.py" 
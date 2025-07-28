#!/bin/bash
# =============================================================================
# CREWAI → LANGGRAPH MIGRATION INVESTIGATION SCRIPT
# =============================================================================
# Purpose: Determine if Guide 1 "CrewAI → LangGraph Migration" was accomplished
# For: Senior Engineer to execute and document findings
# Expected Runtime: 5-10 minutes
# =============================================================================

echo "🔍 AUREN CrewAI Migration Investigation Tool"
echo "=========================================="
echo "This script will help determine if NEUROS was migrated from CrewAI to LangGraph"
echo ""

# Initialize findings report
REPORT_FILE="crewai_migration_findings.md"
echo "# CrewAI → LangGraph Migration Investigation Report" > $REPORT_FILE
echo "Generated: $(date)" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# =============================================================================
# SECTION 1: Check for CrewAI Dependencies
# =============================================================================

echo "1️⃣ Checking for CrewAI dependencies..."
echo "## 1. CrewAI Dependencies Check" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Check requirements files
echo "### Requirements Files:" >> $REPORT_FILE
for req_file in requirements.txt requirements.dev.txt pyproject.toml setup.py; do
    if [ -f "$req_file" ]; then
        echo "Checking $req_file..."
        if grep -i "crewai" "$req_file" > /dev/null 2>&1; then
            echo "✅ FOUND: CrewAI in $req_file" | tee -a $REPORT_FILE
            grep -i "crewai" "$req_file" >> $REPORT_FILE
        else
            echo "❌ NOT FOUND: No CrewAI in $req_file" | tee -a $REPORT_FILE
        fi
        echo "" >> $REPORT_FILE
    fi
done

# Check pip freeze in containers
echo "### Docker Container Dependencies:" >> $REPORT_FILE
if command -v docker &> /dev/null; then
    for container in $(docker ps --format "{{.Names}}" | grep -E "auren|biometric"); do
        echo "Checking container: $container"
        if docker exec $container pip list 2>/dev/null | grep -i crewai; then
            echo "✅ FOUND: CrewAI installed in $container" | tee -a $REPORT_FILE
        else
            echo "❌ NOT FOUND: No CrewAI in $container" | tee -a $REPORT_FILE
        fi
    done
fi
echo "" >> $REPORT_FILE

# =============================================================================
# SECTION 2: Search for CrewAI Code Artifacts
# =============================================================================

echo -e "\n2️⃣ Searching for CrewAI code artifacts..."
echo "## 2. CrewAI Code Artifacts" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Define search patterns
CREWAI_PATTERNS=(
    "from crewai import"
    "import crewai"
    "CrewAI"
    "class.*Agent.*CrewAI"
    "crew\.Agent"
    "crew\.Task"
    "crew\.Crew"
)

# Search for CrewAI imports and usage
echo "### CrewAI Import/Usage Patterns:" >> $REPORT_FILE
for pattern in "${CREWAI_PATTERNS[@]}"; do
    echo "Searching for: $pattern"
    results=$(find . -type f \( -name "*.py" -o -name "*.yaml" \) \
        -not -path "./venv/*" \
        -not -path "./.git/*" \
        -not -path "./node_modules/*" \
        -exec grep -l "$pattern" {} \; 2>/dev/null)
    
    if [ -n "$results" ]; then
        echo "✅ FOUND files with '$pattern':" | tee -a $REPORT_FILE
        echo "$results" | tee -a $REPORT_FILE
        echo "" >> $REPORT_FILE
        
        # Show context
        echo "Context:" >> $REPORT_FILE
        for file in $results; do
            echo "File: $file" >> $REPORT_FILE
            grep -n -C 2 "$pattern" "$file" >> $REPORT_FILE 2>/dev/null
            echo "---" >> $REPORT_FILE
        done
    else
        echo "❌ NOT FOUND: No files with '$pattern'" | tee -a $REPORT_FILE
    fi
done
echo "" >> $REPORT_FILE

# =============================================================================
# SECTION 3: Check for Migration Scripts
# =============================================================================

echo -e "\n3️⃣ Looking for migration scripts or guides..."
echo "## 3. Migration Scripts/Guides" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Search for migration-related files
MIGRATION_PATTERNS=(
    "migrate"
    "migration"
    "crewai.*langgraph"
    "convert.*agent"
    "wrapper"
    "adapter"
)

echo "### Migration-Related Files:" >> $REPORT_FILE
for pattern in "${MIGRATION_PATTERNS[@]}"; do
    files=$(find . -type f -iname "*${pattern}*" \
        -not -path "./venv/*" \
        -not -path "./.git/*" \
        -not -path "./migrations/*" 2>/dev/null | grep -v "__pycache__")
    
    if [ -n "$files" ]; then
        echo "Found files matching '$pattern':" | tee -a $REPORT_FILE
        echo "$files" | tee -a $REPORT_FILE
        echo "" >> $REPORT_FILE
    fi
done

# =============================================================================
# SECTION 4: Analyze NEUROS Implementation
# =============================================================================

echo -e "\n4️⃣ Analyzing NEUROS implementation..."
echo "## 4. NEUROS Implementation Analysis" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Find NEUROS-related files
NEUROS_FILES=$(find . -type f \( -name "*neuros*" -o -name "*NEUROS*" \) \
    -name "*.py" -not -path "./venv/*" -not -path "./.git/*" 2>/dev/null)

echo "### NEUROS Files Found:" >> $REPORT_FILE
echo "$NEUROS_FILES" | tee -a $REPORT_FILE
echo "" >> $REPORT_FILE

# Check if NEUROS uses LangGraph
echo "### NEUROS LangGraph Usage:" >> $REPORT_FILE
for file in $NEUROS_FILES; do
    if [ -f "$file" ]; then
        echo "Checking $file..." | tee -a $REPORT_FILE
        
        # Check for LangGraph imports
        if grep -E "(from langgraph|import.*langgraph|StateGraph|MessageGraph)" "$file" > /dev/null 2>&1; then
            echo "✅ Uses LangGraph" | tee -a $REPORT_FILE
            grep -n -E "(from langgraph|import.*langgraph|StateGraph|MessageGraph)" "$file" >> $REPORT_FILE
        else
            echo "❌ No LangGraph imports found" | tee -a $REPORT_FILE
        fi
        
        # Check for CrewAI imports
        if grep -E "(from crewai|import.*crewai)" "$file" > /dev/null 2>&1; then
            echo "⚠️  Contains CrewAI imports!" | tee -a $REPORT_FILE
            grep -n -E "(from crewai|import.*crewai)" "$file" >> $REPORT_FILE
        else
            echo "✅ No CrewAI imports" | tee -a $REPORT_FILE
        fi
        echo "" >> $REPORT_FILE
    fi
done

# =============================================================================
# SECTION 5: Check Version Control History
# =============================================================================

echo -e "\n5️⃣ Checking version control for migration evidence..."
echo "## 5. Version Control History" >> $REPORT_FILE
echo "" >> $REPORT_FILE

if [ -d ".git" ]; then
    echo "### Git Log Analysis:" >> $REPORT_FILE
    
    # Search for migration-related commits
    echo "Migration-related commits:" >> $REPORT_FILE
    git log --grep="crewai\|CrewAI\|migration\|migrate" --oneline -n 20 >> $REPORT_FILE 2>/dev/null || echo "No migration commits found" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    
    # Check for deleted CrewAI files
    echo "### Deleted CrewAI Files:" >> $REPORT_FILE
    git log --diff-filter=D --summary | grep -B 2 -i "crewai" >> $REPORT_FILE 2>/dev/null || echo "No deleted CrewAI files found" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    
    # Look for file renames
    echo "### File Renames (potential migrations):" >> $REPORT_FILE
    git log --name-status --follow --grep="neuros\|NEUROS" | grep "^R" >> $REPORT_FILE 2>/dev/null || echo "No relevant renames found" >> $REPORT_FILE
else
    echo "No .git directory found" >> $REPORT_FILE
fi
echo "" >> $REPORT_FILE

# =============================================================================
# SECTION 6: Documentation Search
# =============================================================================

echo -e "\n6️⃣ Searching documentation for migration evidence..."
echo "## 6. Documentation Analysis" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Search for migration documentation
DOC_PATTERNS=(
    "CrewAI"
    "migration"
    "migrate.*from.*crew"
    "wrapper"
    "legacy.*agent"
)

echo "### Documentation Mentions:" >> $REPORT_FILE
for pattern in "${DOC_PATTERNS[@]}"; do
    docs=$(find . -type f \( -name "*.md" -o -name "*.rst" -o -name "*.txt" \) \
        -not -path "./venv/*" \
        -not -path "./.git/*" \
        -exec grep -l -i "$pattern" {} \; 2>/dev/null)
    
    if [ -n "$docs" ]; then
        echo "Found in documentation - '$pattern':" | tee -a $REPORT_FILE
        for doc in $docs; do
            echo "  File: $doc" >> $REPORT_FILE
            grep -n -i -C 1 "$pattern" "$doc" | head -20 >> $REPORT_FILE
            echo "  ..." >> $REPORT_FILE
        done
        echo "" >> $REPORT_FILE
    fi
done

# =============================================================================
# SECTION 7: Implementation Timeline Analysis
# =============================================================================

echo -e "\n7️⃣ Analyzing implementation timeline..."
echo "## 7. Implementation Timeline" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Get creation dates of key files
echo "### Key File Creation Dates:" >> $REPORT_FILE
for pattern in "*neuros*.py" "*langgraph*.py" "*crew*.py" "section_8*.py"; do
    files=$(find . -name "$pattern" -type f -not -path "./venv/*" 2>/dev/null)
    for file in $files; do
        if [ -f "$file" ]; then
            # Get file creation date from git
            first_commit=$(git log --follow --format="%ai %s" --reverse "$file" 2>/dev/null | head -1)
            if [ -n "$first_commit" ]; then
                echo "$file: $first_commit" >> $REPORT_FILE
            else
                # Fallback to file modification time
                echo "$file: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null)" >> $REPORT_FILE
            fi
        fi
    done
done
echo "" >> $REPORT_FILE

# =============================================================================
# SECTION 8: Final Analysis & Conclusion
# =============================================================================

echo -e "\n8️⃣ Generating final analysis..."
echo "## 8. Final Analysis & Conclusion" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Count evidence
CREWAI_EVIDENCE=0
LANGGRAPH_EVIDENCE=0
MIGRATION_EVIDENCE=0

# Analyze findings
if grep -q "✅ FOUND: CrewAI" $REPORT_FILE; then
    ((CREWAI_EVIDENCE++))
fi

if grep -q "✅ Uses LangGraph" $REPORT_FILE; then
    ((LANGGRAPH_EVIDENCE++))
fi

if grep -q "migration\|migrate" $REPORT_FILE | grep -v "Investigation"; then
    ((MIGRATION_EVIDENCE++))
fi

echo "### Evidence Summary:" >> $REPORT_FILE
echo "- CrewAI Evidence Found: $CREWAI_EVIDENCE indicators" >> $REPORT_FILE
echo "- LangGraph Evidence Found: $LANGGRAPH_EVIDENCE indicators" >> $REPORT_FILE
echo "- Migration Evidence Found: $MIGRATION_EVIDENCE indicators" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "### Conclusion:" >> $REPORT_FILE
if [ $CREWAI_EVIDENCE -gt 0 ] && [ $MIGRATION_EVIDENCE -gt 0 ]; then
    echo "✅ **MIGRATION LIKELY OCCURRED**: Found evidence of both CrewAI usage and migration artifacts." >> $REPORT_FILE
elif [ $CREWAI_EVIDENCE -eq 0 ] && [ $LANGGRAPH_EVIDENCE -gt 0 ]; then
    echo "❌ **NO MIGRATION NEEDED**: NEUROS appears to be built directly in LangGraph without CrewAI heritage." >> $REPORT_FILE
elif [ $CREWAI_EVIDENCE -gt 0 ] && [ $MIGRATION_EVIDENCE -eq 0 ]; then
    echo "⚠️  **MIGRATION INCOMPLETE**: Found CrewAI code but no migration evidence." >> $REPORT_FILE
else
    echo "❓ **INCONCLUSIVE**: Insufficient evidence to determine migration status." >> $REPORT_FILE
fi
echo "" >> $REPORT_FILE

# =============================================================================
# SECTION 9: Recommendations
# =============================================================================

echo "## 9. Recommendations for Senior Engineer" >> $REPORT_FILE
echo "" >> $REPORT_FILE
echo "1. Review the NEUROS implementation files listed above" >> $REPORT_FILE
echo "2. Check if any CrewAI agents exist outside of NEUROS" >> $REPORT_FILE
echo "3. Interview the development team about original implementation" >> $REPORT_FILE
echo "4. If CrewAI code exists, determine if migration guide is still needed" >> $REPORT_FILE
echo "5. Document the final decision in the project README" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# =============================================================================
# COMPLETION
# =============================================================================

echo -e "\n✅ Investigation complete!"
echo "📄 Full report saved to: $REPORT_FILE"
echo ""
echo "Quick Summary:"
tail -n 20 $REPORT_FILE | grep -A 5 "### Conclusion:"

# Open report in default editor if available
if command -v code &> /dev/null; then
    echo -e "\nOpening report in VS Code..."
    code $REPORT_FILE
elif command -v vim &> /dev/null; then
    echo -e "\nOpening report in vim..."
    vim $REPORT_FILE
else
    echo -e "\nPlease review the report at: $REPORT_FILE"
fi

# =============================================================================
# QUICK CHECK COMMANDS FOR SENIOR ENGINEER
# =============================================================================

cat << 'EOF' > quick_checks.sh
#!/bin/bash
# Quick checks for Senior Engineer

echo "🔍 Quick CrewAI Migration Checks"
echo "================================"

# 1. Is CrewAI installed?
echo -n "CrewAI installed: "
pip list | grep -i crewai || echo "NO"

# 2. Any CrewAI imports?
echo -n "CrewAI imports found: "
find . -name "*.py" -exec grep -l "from crewai\|import crewai" {} \; 2>/dev/null | wc -l

# 3. NEUROS using LangGraph?
echo -n "NEUROS using LangGraph: "
find . -name "*neuros*.py" -exec grep -l "langgraph" {} \; 2>/dev/null | head -1 || echo "NO"

# 4. Migration scripts exist?
echo -n "Migration scripts: "
find . -name "*migrat*.py" -o -name "*convert*.py" | grep -i crew | wc -l

echo "================================"
EOF

chmod +x quick_checks.sh

echo -e "\n💡 Also created quick_checks.sh for rapid verification"

# =============================================================================
# END OF INVESTIGATION SCRIPT
# ============================================================================= 
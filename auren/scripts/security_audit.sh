#!/bin/bash
# Additional security audit script

echo "🔐 AUREN Security Audit"

# Check for hardcoded secrets
echo "Checking for hardcoded secrets..."
grep -r -i -E "(api_key|password|secret|token)" src/ --include="*.py" | grep -v -E "(os\.environ|getenv|Config|BaseSettings)" || echo "✅ No hardcoded secrets found"

# Check file permissions
echo -e "\nChecking file permissions..."
find . -type f -perm /o+w -ls 2>/dev/null | grep -v -E "(\.git|__pycache__|\.pyc)" || echo "✅ No world-writable files"

# Check for SQL injection vulnerabilities
echo -e "\nChecking for SQL injection risks..."
grep -r -E "(execute|executemany|executescript)\s*\(" src/ --include="*.py" | grep -v -E "(parameterized|prepared|bind)" || echo "✅ No direct SQL execution found"

echo -e "\n✅ Security audit complete" 
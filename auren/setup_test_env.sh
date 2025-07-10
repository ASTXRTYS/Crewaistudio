#!/bin/bash
echo "🔧 Setting up AUREN test environment"

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create pytest configuration
cat > pytest.ini << EOF
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
pythonpath = .
EOF

# Update test imports to use proper paths
if [ -d "tests" ]; then
    find tests -name "*.py" -exec sed -i '' 's/from auren\.src\./from src\./g' {} \;
else
    echo "⚠️  No tests directory found"
fi

echo "✅ Test environment configured" 
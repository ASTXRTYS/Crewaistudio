#!/bin/bash

echo "🔍 AUREN Code Quality Check"

# 1. Install dev dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# 2. Format code
echo "Formatting code..."
black src/ tests/ --line-length 100
isort src/ tests/

# 3. Type checking
echo "Type checking..."
mypy src/ --ignore-missing-imports --strict

# 4. Security scan
echo "Security scanning..."
bandit -r src/ -ll

# 5. Linting
echo "Linting..."
flake8 src/ --max-line-length=100 --ignore=E203,W503

# 6. Test coverage
echo "Running tests with coverage..."
pytest tests/ --cov=src --cov-report=html --cov-report=term

echo "✅ Quality check complete" 
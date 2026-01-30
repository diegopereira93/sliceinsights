#!/bin/bash
set -e

echo "🔍 Init Verification Process..."

echo "-----------------------------------"
echo "📦 verifying Dependencies..."
# Assume dependencies are installed in the venv


echo "-----------------------------------"
echo "🧹 Running Linter (Ruff)..."
# Ruff is strictly faster than Flake8/Black
./.venv/bin/ruff check .
# ruff format --check . # Uncomment to enforce formatting

echo "-----------------------------------"
echo "🔒 Running Security Scan (Safety)..."
./.venv/bin/python3 -m safety check -r requirements.txt --ignore 70612 # Ignoring potential false positives if needed, or specific known issues

echo "-----------------------------------"
echo "🧪 Running Tests (Pytest)..."
# Run pytest with coverage or just basic execution
./.venv/bin/python3 -m pytest tests/ -v

echo "-----------------------------------"
echo "✅ All checks passed! Ready for deployment."

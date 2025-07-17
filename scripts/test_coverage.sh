#!/bin/bash
# Test coverage script for site-backup

set -e

echo "🧪 Running tests with coverage..."
uv run pytest

echo ""
echo "📊 Coverage Summary:"
uv run coverage report

echo ""
echo "📝 Generating HTML coverage report..."
uv run coverage html

echo ""
echo "✅ Coverage analysis complete!"
echo "📖 Open htmlcov/index.html to view detailed coverage report"
echo "💡 Tip: Use 'make test-cov-html' to run tests and open the report automatically"

# Check if coverage is below threshold
COVERAGE_THRESHOLD=80
COVERAGE_PERCENT=$(uv run coverage report --format=total)

if (( $(echo "$COVERAGE_PERCENT < $COVERAGE_THRESHOLD" | bc -l) )); then
    echo "⚠️  Warning: Coverage ($COVERAGE_PERCENT%) is below threshold ($COVERAGE_THRESHOLD%)"
    exit 1
else
    echo "✅ Coverage ($COVERAGE_PERCENT%) meets threshold ($COVERAGE_THRESHOLD%)"
fi

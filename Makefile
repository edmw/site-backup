# Makefile for site-backup project
# Run with: make <target>

.PHONY: help install test test-no-cov test-unit test-integration test-cov-html cov-report cov-html cov-xml clean-cov lint format check clean build release

# Default target
help:
	@echo
	@echo "💡💡💡 Targets:"
	@echo "  install        - Install dependencies"
	@echo "  test           - Run tests with coverage"
	@echo "  test-no-cov    - Run tests without coverage"
	@echo "  test-unit      - Run only unit tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  test-cov-html  - Run tests and open HTML coverage report"
	@echo "  cov-report     - Show coverage report in terminal"
	@echo "  cov-html       - Generate HTML coverage report"
	@echo "  cov-xml        - Generate XML coverage report (for CI)"
	@echo "  clean-cov      - Clean coverage files"
	@echo "  lint           - Run ruff linting"
	@echo "  format         - Format code with black"
	@echo "  check          - Run all quality checks (lint + test)"
	@echo "  clean          - 🧹 Clean all generated files"
	@echo "  build          - 🚧 Build distribution package"
	@echo "  release        - 🚀 Prepare for release"

# Install dependencies
install:
	uv sync

# Run tests with coverage
test:
	uv run pytest

# Run tests without coverage
test-no-cov:
	uv run pytest --no-cov

# Run only unit tests
test-unit:
	uv run pytest -m unit

# Run only integration tests
test-integration:
	uv run pytest -m integration

# Run tests with coverage and open HTML report
test-cov-html: test
	open htmlcov/index.html

# Run coverage report in terminal
cov-report:
	uv run coverage report

# Generate coverage HTML report
cov-html:
	uv run coverage html

# Generate coverage XML report (for CI)
cov-xml:
	uv run coverage xml

# Clean coverage files
clean-cov:
	@rm -rf htmlcov/
	@rm -f coverage.xml
	@rm -f .coverage

# Run linting
lint:
	uv run ruff check backup/ sitebackup.py tests/

# Format code
format:
	uv run black backup/ sitebackup.py tests/

# Run all quality checks
check: lint test

# Clean all generated files
clean: clean-cov
	@echo "🧹🧹🧹 Clean project ..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete

# Build distribution package
build:
	@echo "🚧🚧🚧 Build project ..."
	@uv build
	@WHEEL_FILE=$$(ls dist/*-$(shell grep '^version = ' pyproject.toml | cut -d'"' -f2)-py3-none-any.whl); \
		unzip -t "$$WHEEL_FILE"

# Prepare for release
release: clean build
	@echo "🚀🚀🚀 Release project ..."
	@ls -l dist/
	@echo "💡💡💡 Ready for GitHub release upload"

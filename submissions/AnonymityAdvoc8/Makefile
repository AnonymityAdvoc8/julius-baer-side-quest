# Banking Client Makefile
# Requires Python 3.12+

# Python executables
PYTHON := python3.12
PIP := pip3.12

# Virtual environment
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

.PHONY: help venv install install-dev test test-unit test-integration coverage format lint type-check clean clean-all run docker-build docker-up docker-down docker-test health-check

help:
	@echo "🏦 Banking Client - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make venv             Create Python 3.12 virtual environment"
	@echo "  make install          Install production dependencies (requires venv)"
	@echo "  make install-dev      Install development dependencies (requires venv)"
	@echo "  make setup            Complete setup (venv + install)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make coverage         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           Format code with black"
	@echo "  make lint             Lint code with ruff"
	@echo "  make type-check       Type check with mypy"
	@echo ""
	@echo "Running:"
	@echo "  make check-server     Check if banking server is running"
	@echo "  make run ARGS='...'   Run CLI (e.g., ARGS='transfer --from ACC1000 --to ACC1001 --amount 100')"
	@echo "  make demo             Run example usage script"
	@echo "  make health-check     Run comprehensive health check"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-up        Start all services with docker-compose"
	@echo "  make docker-down      Stop all services"
	@echo "  make docker-test      Test Docker setup"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Clean generated files"
	@echo "  make clean-all        Clean everything including venv"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make setup         # Create venv and install dependencies"
	@echo "  2. make test          # Run tests"
	@echo "  3. make demo          # See examples"

# Create virtual environment with Python 3.12
venv:
	@echo "🔧 Creating Python 3.12 virtual environment..."
	@if [ -d "$(VENV)" ]; then \
		echo "⚠️  Virtual environment already exists at $(VENV)"; \
		echo "   Run 'make clean-all' to remove it first"; \
	else \
		$(PYTHON) -m venv $(VENV); \
		echo "✅ Virtual environment created at $(VENV)"; \
		echo ""; \
		echo "To activate manually:"; \
		echo "  source $(VENV_BIN)/activate"; \
	fi

# Check if venv exists
check-venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found!"; \
		echo "   Run 'make venv' or 'make setup' first"; \
		exit 1; \
	fi

# Install production dependencies
install: check-venv
	@echo "📦 Installing production dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	@echo "✅ Production dependencies installed"

# Install development dependencies
install-dev: check-venv
	@echo "📦 Installing development dependencies..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements-dev.txt
	@echo "✅ Development dependencies installed"

# Complete setup (venv + dependencies)
setup:
	@echo "🚀 Running complete setup..."
	@make venv
	@make install-dev
	@echo ""
	@echo "✅ Setup complete!"
	@echo ""
	@echo "To activate the virtual environment:"
	@echo "  source $(VENV_BIN)/activate"
	@echo ""
	@echo "To run the client:"
	@echo "  make run ARGS='transfer --from ACC1000 --to ACC1001 --amount 100'"
	@echo "  make demo"

# Run all tests
test: check-venv
	@echo "🧪 Running all tests..."
	$(VENV_PYTHON) -m pytest

# Run unit tests only
test-unit: check-venv
	@echo "🧪 Running unit tests..."
	$(VENV_PYTHON) -m pytest tests/test_client.py -v

# Run integration tests only
test-integration: check-venv
	@echo "🧪 Running integration tests..."
	$(VENV_PYTHON) -m pytest tests/test_integration.py -v

# Run tests with coverage
coverage: check-venv
	@echo "📊 Running tests with coverage..."
	$(VENV_PYTHON) -m pytest --cov=banking_client --cov-report=html --cov-report=term
	@echo ""
	@echo "📄 Coverage report generated in htmlcov/index.html"

# Format code
format: check-venv
	@echo "🎨 Formatting code with black..."
	$(VENV_PYTHON) -m black banking_client/ tests/ main.py example_usage.py

# Lint code
lint: check-venv
	@echo "🔍 Linting code with ruff..."
	$(VENV_PYTHON) -m ruff check banking_client/ tests/ main.py

# Type check
type-check: check-venv
	@echo "🔍 Type checking with mypy..."
	$(VENV_PYTHON) -m mypy banking_client/

# Run CLI
run: check-venv
	@if [ -z "$(ARGS)" ]; then \
		echo "❌ Please provide ARGS"; \
		echo "Example: make run ARGS='transfer --from ACC1000 --to ACC1001 --amount 100'"; \
		exit 1; \
	fi
	$(VENV_PYTHON) main.py $(ARGS)

# Check if server is running
check-server: check-venv
	@echo "🔍 Checking if banking server is running..."
	@$(VENV_PYTHON) check_server.py

# Run demo script
demo: check-venv
	@echo "🎬 Running example usage demo..."
	@$(VENV_PYTHON) example_usage.py

# Health check
health-check: check-venv
	@echo "🏥 Running health check..."
	@$(VENV_PYTHON) health_check.py --verbose

# Docker build
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t banking-client:latest .

# Docker compose up
docker-up:
	@echo "🐳 Starting services with docker-compose..."
	docker-compose up -d
	@echo ""
	@echo "✅ Services started!"
	@echo "Run: docker-compose run --rm banking-client transfer --from ACC1000 --to ACC1001 --amount 100"

# Docker compose down
docker-down:
	@echo "🐳 Stopping docker-compose services..."
	docker-compose down

# Test Docker setup
docker-test: docker-build
	@echo "🧪 Testing Docker image..."
	docker run --rm banking-client:latest --help
	@echo ""
	@echo "✅ Docker image works!"

# Clean generated files
clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf __pycache__ banking_client/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache .ruff_cache
	rm -rf *.egg-info build/ dist/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

# Clean everything including venv
clean-all: clean
	@echo "🧹 Removing virtual environment..."
	rm -rf $(VENV)
	@echo "✅ Everything cleaned"

# Example usage (will be shown in help)
.PHONY: examples
examples:
	@echo "Example Commands:"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  make setup                                    # Complete setup"
	@echo ""
	@echo "Transfer Funds:"
	@echo "  make run ARGS='transfer --from ACC1000 --to ACC1001 --amount 100'"
	@echo ""
	@echo "Validate Account:"
	@echo "  make run ARGS='validate --account ACC1000'"
	@echo ""
	@echo "Check Balance:"
	@echo "  make run ARGS='balance --account ACC1000'"
	@echo ""
	@echo "List Accounts:"
	@echo "  make run ARGS='list'"
	@echo ""
	@echo "Run with Verbose Logging:"
	@echo "  make run ARGS='--verbose transfer --from ACC1000 --to ACC1001 --amount 50'"


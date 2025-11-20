# Test targets

.PHONY: test test-unit test-integration test-cov test-watch

# Run all tests
test:
	@echo "Running all tests..."
	uv run pytest tests/ -v

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	uv run pytest tests/unit/ -v

# Run integration tests only
test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/integration/ -v

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	uv run pytest tests/ -v --cov=scripts --cov-report=term-missing --cov-report=html

# Watch mode (requires pytest-watch, add to dev-dependencies if needed)
test-watch:
	@echo "Running tests in watch mode..."
	uv run pytest-watch scripts/tests/ -v


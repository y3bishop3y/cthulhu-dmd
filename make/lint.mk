# Linting and type checking targets

.PHONY: lint
lint: $(VENV) ## Run all linting checks (ruff check, ruff format, mypy)
	@echo "Running linting checks..."
	$(PYTHON) -m ruff check scripts/
	@echo "✓ Ruff check passed"
	$(PYTHON) -m ruff format scripts/ --check
	@echo "✓ Ruff format passed"
	$(PYTHON) -m mypy scripts/ --ignore-missing-imports
	@echo "✓ Mypy passed"
	@echo "All linting checks passed!"

.PHONY: lint-fix
lint-fix: $(VENV) ## Auto-fix linting issues (ruff format)
	@echo "Fixing formatting..."
	$(PYTHON) -m ruff format scripts/
	@echo "Formatting fixed!"

.PHONY: type-check
type-check: $(VENV) ## Run mypy type checking
	@echo "Running type checks..."
	$(PYTHON) -m mypy scripts/ --ignore-missing-imports
	@echo "✓ Type checking passed"

.PHONY: format
format: $(VENV) ## Format code with ruff
	@echo "Formatting code..."
	$(PYTHON) -m ruff format scripts/
	@echo "Code formatted!"


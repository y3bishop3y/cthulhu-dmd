# Setup targets for virtual environment and dependencies

.PYTHON := python3
UV := uv
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: setup
setup: $(VENV) ## Create/update .venv and install all project dependencies
	@echo "Installing project dependencies..."
	@if [ -f "pyproject.toml" ]; then \
		if [ -d "cthulhu_dmd" ] || [ -d "src/cthulhu_dmd" ] || [ -f "setup.py" ]; then \
			echo "Installing project and dependencies with uv sync..."; \
			$(UV) sync || true; \
		else \
			echo "Installing dependencies from pyproject.toml..."; \
			if [ -f "uv.lock" ]; then \
				$(UV) sync 2>/dev/null || $(UV) pip install -r uv.lock 2>/dev/null || true; \
			else \
				echo "Generating lock file and installing dependencies..."; \
				$(UV) lock 2>/dev/null && $(UV) sync 2>/dev/null || \
				($(UV) pip install $(shell grep -A 100 '^\[project\]' pyproject.toml | grep -E '^\s*dependencies\s*=' | head -1 | sed 's/.*=\s*\[\(.*\)\].*/\1/' | tr -d '"' | tr ',' ' ') 2>/dev/null || echo "No dependencies to install"); \
			fi \
		fi \
	else \
		echo "No pyproject.toml found"; \
	fi
	@echo "Setup complete! Virtual environment ready at $(VENV)"
	@echo "Activate with: source $(VENV)/bin/activate"

.PHONY: venv
venv: $(VENV) ## Create virtual environment if it doesn't exist

$(VENV):
	@echo "Creating virtual environment at $(VENV)..."
	$(UV) venv
	@echo "Virtual environment created successfully"

.PHONY: install
install: $(VENV) ## Install dependencies (alias for setup)
	$(MAKE) setup

.PHONY: update
update: $(VENV) ## Update dependencies from pyproject.toml
	@echo "Updating dependencies..."
	@if [ -f "pyproject.toml" ]; then \
		if [ -d "cthulhu_dmd" ] || [ -d "src/cthulhu_dmd" ] || [ -f "setup.py" ]; then \
			$(UV) sync || true; \
		else \
			$(UV) lock && $(UV) sync 2>/dev/null || echo "Updated lock file. Run 'make setup' to install dependencies."; \
		fi \
		echo "Dependencies updated"; \
	else \
		echo "No pyproject.toml found"; \
	fi

.PHONY: clean-venv
clean-venv: ## Remove the virtual environment
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Virtual environment removed"

.PHONY: check-venv
check-venv: ## Check if virtual environment exists
	@if [ -d "$(VENV)" ]; then \
		echo "Virtual environment exists at $(VENV)"; \
		$(PYTHON) --version; \
	else \
		echo "Virtual environment not found. Run 'make setup' to create it."; \
		exit 1; \
	fi

.PHONY: shell
shell: setup ## Activate the virtual environment in a new shell (like 'poetry shell')
	@echo "Activating virtual environment in a new shell..."
	@echo "Type 'exit' to return to your original shell."
	@echo ""
	@if [ ! -d "$(VENV)" ]; then \
		echo "Error: Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@exec zsh -c "cd '$(PWD)' && source $(VENV)/bin/activate && export VIRTUAL_ENV='$(PWD)/$(VENV)' && export PATH='$(PWD)/$(VENV)/bin:$$PATH' && exec zsh -i"


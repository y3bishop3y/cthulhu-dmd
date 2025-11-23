# Website generation and serving targets

.PHONY: site-generate site-serve site-up site-help

site-generate: ## Generate website data files from character JSON
	@echo "Generating website data files..."
	uv run python sites/scripts/generate_site.py

site-serve: ## Start local development server (port 8000)
	@echo "Starting local development server..."
	@echo "Open http://localhost:8000 in your browser"
	@echo "Press Ctrl+C to stop"
	cd sites && python3 -m http.server 8000

site-up: site-generate site-serve ## Generate site data and start development server

site-help: ## Show website-related commands
	@echo "Website Commands:"
	@echo "  make site-generate  - Generate website data files"
	@echo "  make site-serve     - Start local development server"
	@echo "  make site-up        - Generate data and start server"


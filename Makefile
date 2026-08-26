.PHONY: dev ingest benchmark dashboard setup

setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi

dev: setup
	uvicorn src.api.main:app --reload

ingest:
	@echo "Ingestion task triggered."

benchmark:
	python benchmarks/run_benchmark.py

dashboard:
	cd dashboard && npm run dev
.PHONY: dev ingest benchmark dashboard test test-backend test-frontend test-all build install

dev:
	@echo "Starting dev server (uvicorn)..."
	uvicorn src.api.main:app --reload --port 8000

ingest:
	@echo "Run ingestion (placeholder)"
	python -c "print('ingest placeholder')"

benchmark:
	@echo "Run benchmarks (placeholder)"
	python -c "print('benchmark placeholder')"

dashboard:
	@echo "Installing dashboard dependencies..."
	cd dashboard && pnpm install

test-backend:
	@echo "Running backend tests..."
	uv run pytest tests/backend/ -v

test-frontend:
	@echo "Running frontend tests..."
	cd dashboard && pnpm test

test-all: test-backend test-frontend
	@echo "All tests passed!"

test: test-all

build: build-frontend build-backend

build-backend:
	@echo "Building backend..."

build-frontend:
	cd dashboard && pnpm build

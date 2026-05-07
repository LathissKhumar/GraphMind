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

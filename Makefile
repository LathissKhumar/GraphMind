.PHONY: dev ingest benchmark dashboard test clean install

install:
	@pip install -e .

dev:
	@uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

ingest:
	@python -m src.graph.ingestion

benchmark:
	@python benchmarks/run_benchmark.py

dashboard:
	@cd dashboard && npm run dev

test:
	@pytest tests/

clean:
	@rm -rf src/__pycache__ .pytest_cache .coverage htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
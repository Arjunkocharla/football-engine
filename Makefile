.PHONY: install install-dev run lint format test check migrate migrate-down simulate

PYTHON ?= .venv/bin/python

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m uvicorn football_engine.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	$(PYTHON) -m ruff check src tests

format:
	$(PYTHON) -m black src tests

test:
	$(PYTHON) -m pytest -q

check: lint test

migrate:
	$(PYTHON) -m alembic upgrade head

migrate-down:
	$(PYTHON) -m alembic downgrade -1

simulate:
	$(PYTHON) scripts/run_simulator.py --base-url http://localhost:8000

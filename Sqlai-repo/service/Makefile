.PHONY: bootstrap seed dev test policy-test check clean docker

PY ?= python3
VENV ?= .venv
BIN = $(VENV)/bin

bootstrap:            ## create the virtualenv and install dependencies
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -q -e ".[dev]"

seed:                 ## create the local DuckDB warehouse with fictional data
	$(BIN)/python -m sqlai.demo_data data/warehouse.duckdb

dev: seed             ## run the API on http://127.0.0.1:8000 (docs at /docs)
	SQLAI_ENV=local $(BIN)/python -m sqlai

test:                 ## full test suite
	$(BIN)/python -m pytest -p no:warnings

policy-test:          ## policy golden tests only
	$(BIN)/python -m pytest -p no:warnings tests/test_golden.py

check:                ## byte-compile and run tests
	$(BIN)/python -m compileall -q sqlai
	$(MAKE) test

docker:               ## build the container image
	docker build -t sqlai:phase1 .

clean:
	rm -rf data .pytest_cache **/__pycache__

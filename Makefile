.PHONY: help install install-dev lint format typecheck test test-cov circuits setup clean

PYTHON ?= python
PYTEST ?= pytest
RUFF   ?= ruff

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(PYTHON) -m pip install -r requirements.txt

install-dev: ## Install development dependencies
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

lint: ## Run linter
	$(RUFF) check src/ tests/

format: ## Format code
	$(RUFF) format src/ tests/

typecheck: ## Run type checker
	mypy src/

test: ## Run all tests
	$(PYTEST) tests/ -v

test-cov: ## Run tests with coverage
	$(PYTEST) tests/ --cov=src --cov-report=html --cov-report=term-missing

circuits: ## Compile circuits and run trusted setup
	bash circuits/scripts/compile_circuit.sh
	bash circuits/scripts/trusted_setup.sh

setup: install-dev circuits ## Full project setup

clean: ## Remove build artifacts
	rm -rf circuits/build/*.r1cs circuits/build/*.wasm circuits/build/*.wtns
	rm -rf __pycache__ .pytest_cache htmlcov .mypy_cache .ruff_cache
	rm -rf *.egg-info dist build
	find . -type d -name __pycache__ -exec rm -rf {} +

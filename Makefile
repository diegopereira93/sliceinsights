.PHONY: lint test security clean install

VENV_BIN = .venv/bin
PYTHON = $(VENV_BIN)/python3
PIP = $(VENV_BIN)/pip
RUFF = $(VENV_BIN)/ruff
PYTEST = $(VENV_BIN)/pytest

install:
	$(PIP) install -r requirements.txt

lint:
	$(RUFF) check .

test:
	$(PYTEST)

security:
	$(PYTHON) .agent/skills/vulnerability-scanner/scripts/security_scan.py .

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

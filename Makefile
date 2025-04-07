.PHONY: test lint readme pre-commit

PYTHON_MODULES := reposcore

VENV := .venv
VIRTUALENV := -m venv

DEFAULT_PYTHON := $(shell which python3)
PYTHON := env PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

VERSION := $(shell grep '__version__' reposcore/__init__.py |cut -d'"' -f 2)

version:
	@echo $(VERSION)

venv:
	test -d $(VENV) || $(DEFAULT_PYTHON) $(VIRTUALENV) $(VENV)

requirements: venv
	$(PIP) install -r requirements.txt -r requirements-dev.txt

test: requirements
	$(PYTEST) tests

# README 동기화
readme:
	python scripts/generate_readme.py

# PR 전에 자동으로 README 검증
pre-commit: readme

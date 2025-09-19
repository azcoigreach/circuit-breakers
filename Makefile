.PHONY: install format lint test dev run

install:
pip install -e .[dev]

format:
black app tests

lint:
ruff check app tests
ruff format --check app tests

lint-fix:
ruff check --fix app tests
ruff format app tests

mypy:
mypy app

test:
pytest

dev:
uvicorn app.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

run:
uvicorn app.app:create_app --factory --host 0.0.0.0 --port 8000


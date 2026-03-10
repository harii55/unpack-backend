.PHONY: dev test lint fmt

dev:
	PYTHONPATH=src uv run litestar --app app.main:app run

test:
	PYTHONPATH=src uv run pytest

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

.PHONY: install lint test run docker-build

install:
	pip install -e ".[dev]"

lint:
	ruff check .

test:
	pytest --cov=app --cov-report=term-missing

run:
	uvicorn app.main:app --reload --port 8000

docker-build:
	docker build -t messenger-auto-reply-bot .

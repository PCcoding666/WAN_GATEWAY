.PHONY: install test clean run

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest --cov=src tests/

run:
	python main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +

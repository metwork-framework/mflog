.DEFAULT: all
.PHONY: all develop test coverage

all:
	echo "nothing here, use one of the following targets:"
	echo "develop, test, coverage, clean"

develop:
	python setup.py develop

clean:
	rm -Rf *.egg-info htmlcov coverage.xml .coverage __pycache__ .pytest_cache mflog/__pycache__ tests/__pycache__

test: clean
	pytest tests/

coverage:
	pytest --cov-report html --cov=mflog tests
	pytest --cov=mflog tests/

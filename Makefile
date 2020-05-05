.DEFAULT: all
.PHONY: all develop test coverage codecov

all:
	echo "nothing here, use one of the following targets:"
	echo "develop, test, coverage, codecov, clean"

develop:
	pip install -r requirements.txt
	python setup.py develop

test: develop
	pip install -r test-requirements.txt
	flake8 .
	pytest

coverage: develop
	pip install -r test-requirements.txt
	pytest --cov-report html --cov=mflog tests --cov-report term

codecov: coverage
	if test "$${CODECOV_TOKEN:-}" != ""; then codecov --token=$${CODECOV_TOKEN}; fi

clean:
	rm -Rf *.egg-info htmlcov coverage.xml .coverage __pycache__ .pytest_cache mflog/__pycache__ tests/__pycache__

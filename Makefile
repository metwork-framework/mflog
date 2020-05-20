.DEFAULT: all
.PHONY: all develop test coverage demo

all:
	echo "nothing here, use one of the following targets:"
	echo "develop, test, coverage, clean"

develop:
	python setup.py develop

clean:
	rm -Rf *.egg-info htmlcov coverage.xml .coverage __pycache__ .pytest_cache mflog/__pycache__ tests/__pycache__
	rm -Rf demo/output
	rm -Rf node_modules
	rm -f package-lock.json
	rm -f demo/demo.svg

test: clean
	pytest tests/

coverage:
	pytest --cov-report html --cov=mflog tests
	pytest --cov=mflog tests/

demo: node_modules/.bin/svgexport
	termtosvg --screen-geometry=82x37 --template=solarized_dark --still-frames --command "python demo/demo.py" demo/output
	LAST=`ls -rt demo/output/*.svg |tail -1` ; cp -f $${LAST} demo/demo.svg
	export PATH=.node_modules/bin/svgexport:$${PATH} ; svgexport demo/demo.svg demo/demo.png
	optipng demo/demo.png
	rm -f demo/demo.svg

node_modules/.bin/svgexport:
	npm install svgexport

clean:
	rm -rf *.egg-info
	rm -rf .eggs

lint:
	flake8 tibanna_cgap

install: 
	poetry install

test:
	pytest -vv ./tests/tibanna

retest:  # runs only failed tests from the last test run.
	pytest -vv --last-failed

update:  # updates dependencies
	poetry update

publish-pypi:
	scripts/publish-pypi

help:
	@make info

info:
	@: $(info Here are some 'make' options:)
	   $(info - Use 'make lint' to check style with flake8.)
	   $(info - Use 'make install' to install dependencies using poetry.)
	   $(info - Use 'make publish-pypi' to publish this library to Pypi)
	   $(info - Use 'make retest' to run failing tests from the previous test run.)
	   $(info - Use 'make test' to run tests with the normal options we use for CI/CD like GA.)
	   $(info - Use 'make update' to update dependencies (and the lock file))
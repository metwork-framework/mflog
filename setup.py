import fastentrypoints  # noqa: F401
from setuptools import setup
from setuptools import find_packages

with open('requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n')
        if (line and not line.startswith('--'))]

with open("README.md") as f:
    long_description = f.read()

# Version "0.0.0" will be replaced by CI when releasing
setup(
    author="Fabien MARTY",
    author_email="fabien.marty@gmail.com",
    name='mflog',
    version="0.0.0",
    license="BSD 3",
    python_requires='>=2.7',
    url="https://github.com/metwork-framework/mflog",
    description="opinionated python (structured) logging library "
    "built on structlog",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "log = mflog.log:main",
        ]
    }
)

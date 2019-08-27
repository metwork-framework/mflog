import fastentrypoints  # noqa: F401
from setuptools import setup
from setuptools import find_packages

with open('requirements.txt') as reqs:
    install_requires = [
        line for line in reqs.read().split('\n')
        if (line and not line.startswith('--')) and (";" not in line)]

setup(
    name='mflog',
    packages=find_packages(),
    install_requires=install_requires,
    url="https://github.com/metwork-framework/mflog",
    entry_points={
        "console_scripts": [
            "log = mflog.log:main",
        ]
    }
)

# Development Note

I am following the official tutorial:

https://docs.python-guide.org/writing/structure/


## Goal

The goal is to provide a repo including a python package named "pddls".
The installation use case would be:

> $ pip install pddls

It should make a script of pddlsc, as well as pddl2json and json2pddl available to run.


## Dependency

The pddls uses a modified version of pddl-lib:
https://github.com/hfoffani/pddl-lib

The modified version is available at:
https://github.com/tatsubori/pddl-lib

In it, we have a pddls syntax extension.

Of course it is not available through PyPi, so it must be installed "unofficially".  While we would like to conflict with the original pddl-lib, we start from a installation from github for simplicity.

> pip install git+https://github.com/tatsubori/pddl-lib

according to: https://pip.pypa.io/en/stable/reference/pip_install/#git. I don't think we need -e/--editable option (editable mode) for pip.


## Command Line Scripts

The pddlsc is a command line script.

We just follow:
https://python-packaging.readthedocs.io/en/latest/command-line-scripts.html
and specify "scripts" options to include scripts/pddlsc as a command line script to be added to the bin directory in PYTHON_PATH, such as miniconda/base/bin.


## Distribution

We use twine to publish our package on PyPl.

https://pypi.org/project/twine/

You may need "conda install twine" depending on the virtual environment.

After updating the version number in setup.py, you may package and publish as follow.

> rm dist/*
> python setup.py sdist bdist_wheel
> twine upload --repository-url https://test.pypi.org/legacy/ dist/*
> twine upload dist/*

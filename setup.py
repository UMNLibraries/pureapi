# -*- coding: utf-8 -*-
from distutils.core import setup

packages = \
['pureapi']

package_data = \
{'': ['*']}

install_requires = \
['addict', 'requests', 'tenacity']

setup_kwargs = {
    'name': 'pureapi',
    'version': '1.2.0',
    'description': "Tools for working with Elsevier's Pure API.",
    'long_description': '# pureapi\n\nTools for working with Elsevier\'s Pure API.\n\n## Usage\n\nPlease see `tests/test_*.py` for now. We freely admit this section of the documentation requires\nmuch improvement.\n\n## Pure API Versions\n\nSuccessfully tested against Pure API versions 5.10.x - 5.12.x.\n\n## Requirements and Recommendations\n\n### Python Versions\n\npureapi requires Python >= 3.\n\n### Environment Variables\n\nTo connect to the Pure server, including when running `tests/test_client.py`, the\n`PURE_API_URL` and `PURE_API_KEY` environment variables must be set. One option is to set them in a \n`.env` file. See `env.dist` for an example.\n\n### pyenv, venv, and poetry \n\nTo install and manage Python versions we use [pyenv](https://github.com/pyenv/pyenv), and to manage\ndependencies we use [poetry](https://poetry.eustace.io/). While alternative tools will work, we document\nhere only the tools we use. We will document the use of other tools if demand arises.\n\nOne way to set up all these tools to work together, for a new project, is to follow the workflow below.\nNote that we prefer to put virtual environments inside the project directory. Note also that we use the\nbuilt-in `venv` module to create virtual environments, and we name their directories `.venv`, because\nthat is what `poetry` does and expects.\n\n* Install pyenv.\n* `pyenv install $python_version`\n* `mkdir $project_dir; cd $project_dir`\n* Create a `.python-version` file, containing `$python_version`. \n* `pip install poetry`\n* `poetry config settings.virtualenvs.in-project true`\n* `python -m venv ./.venv/`\n* `source ./.venv/bin/activate`\n \nNow running commands like `poetry install` or `poetry update` should install packages into the virtual\nenvironment in `./.venv`. Don\'t forget to `deactivate` the virtual environment when finished using it.\nIf the project virtual environment is not activated, `poetry run` and `poetry shell` will activate it.\nWhen using `poetry shell`, exit the shell to deactivate the virtual environment. \n\n## Installing\n\nAdd to `pyproject.toml`:\n\n```\npureapi = {git = "git://github.com/UMNLibraries/pureapi.git"}\n```\n\nTo specify a version, include the `tag` parameter:\n\n```\npureapi = {git = "git://github.com/UMNLibraries/pureapi.git", tag = "1.0.0"}\n```\n\nTo install, run `poetry install`.\n\n## Testing\n\nRun the following, either as arguments\nto `poetry run`, or after running `poetry shell`:\n\n```\npytest tests/test_client.py\npytest tests/test_response.py\n```\n\nOr to run all tests: `pytest`\n\nNote that `tests/test_client.py` includes integration tests that make requests against a Pure server,\nso the environment variables described in\n[Requirements and Recommendations](#requirements-and-recommendations)\nmust be set in order to run those tests.\n\n## Contributing\n\n### Include an updated `setup.py`.\n\nPython package managers, including poetry, will be unable to install a VCS-based package without a \n`setup.py` file in the project root. To generate `setup.py`:\n\n```\npoetry build\ntar -zxf dist/pureapi-1.0.0.tar.gz pureapi-1.0.0/setup.py --strip-components 1\n```\n\n### Do not commit `pyproject.lock`.\n\nTo allow for flexibility in dependency versions, do _not_ commit `pyproject.lock`.\nIf multiple developers encounter problems with conflicting dependency versions, we may\nconsider committing `pyproject.lock` at that point.\n\n\n',
    'author': 'David Naughton',
    'author_email': 'naughton@umn.edu',
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.0.0,<4.0.0',
}


setup(**setup_kwargs)

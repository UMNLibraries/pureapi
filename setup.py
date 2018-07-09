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
    'version': '1.0.0',
    'description': "Tools for working with Elsevier's Pure API.",
    'long_description': '# pureapi\n\nTools for working with Elsevier\'s Pure API.\n\n## Usage\n\nPlease see `tests/test_*.py` for now. We freely admit this section of the documentation requires\nmuch improvement.\n\n## Versions\n\nSuccessfully tested against Pure API versions 5.10.x - 5.12.x.\n\n## Installing\n\n### Requirements and Recommendations\n\npureapi requires Python 3.\n\nTo install and manage Python versions we use [pyenv](https://github.com/pyenv/pyenv) and to manage\ndependencies we use [poetry](https://poetry.eustace.io/). For now, poetry is required. We may consider\nadding support for other dependency management tools if there is considerable demand for them.\n\nTo connect to the Pure server, including when running `tests/test_client.py`, the\n`PURE_API_URL` and `PURE_API_KEY` environment variables must be set. See `env.dist` for\nan example.\n\n### Installing as a Dependency\n\nAdd to `pyproject.toml`:\n\n```\npureapi = {git = "git://github.com/UMNLibraries/pureapi.git", tag = "1.0.0"}\n```\n\n### Installing for Development\n\nClone this repo, but do _not_ commit `pyproject.lock`!\n\n## Testing\n\nAfter [installing for development](#installing-for-development), run the following, either as arguments\nto `poetry run`, or after running `poetry shell`:\n\n```\npytest tests/test_client.py\npytest tests/test_response.py\n```\n\nOr to run all tests: `pytest`\n\nNote that `tests/test_client.py` includes integration tests that make requests against a Pure server,\nso the environment variables described in\n[Requirements and Recommendations](#requirements-and-recommendations)\nmust be set in order to run those tests.\n',
    'author': 'David Naughton',
    'author_email': 'naughton@umn.edu',
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.0.0,<4.0.0',
}


setup(**setup_kwargs)

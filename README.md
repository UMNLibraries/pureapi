# pureapi

Tools for working with Elsevier's Pure API.

## Quick Start

If you set the `PURE_API_DOMAIN` and `PURE_API_KEY` environment variables,
and want to use the latest Pure API version, using this package's client
can be as easy as:

```python
from pureapi import client
response = client.get('research-outputs')
```

For more control, pass a `client.Config` object. For example, to make requests
to two different Pure API servers:

```python
from pureapi.client import Config
response = client.get(
    'persons',
    config=Config(domain='example.com', key='123-abc')
)
test_repsonse = client.get(
    'persons',
    config=Config(domain='test.example.com', key='456-def', version='516')
)
```

All functions that make requests of a Pure API server accept a `config`
parameter. See the documentation for `client.Config` for more details.

### Multi-Request Functions

Many collections may contain too many records to download in a single request.
For downloading large numbers of records in multiple requests, use the
`client.*_all*()` functions. For example, to download all research outputs:

```python
for response in client.get_all('research-outputs'):
   json = response.json()
```

### Record-Transforming Functions

For even more convenience, each `client.*_all()` function has an associated
`*_all_transformed()` function. Instead of yielding HTTP responses, which
typicall contain many records each,these functions yield individual records,
transformed from raw JSON into `addict.Dict` objects. These transformed records
allow easier access to deeply nested fields, and may also ensure that some
critical fields exist in each record, even if they may be `None` or empty by
default.

An example using one of these functions to get the titles of all research
outputs:

```python
for ro in client.get_all_transformed('research-outputs'):
   title = ro.title.value
```

For more details, see the documentation for each module. For more examples, see
`tests/test_*.py`.

## Pure API Versions

Successfully tested against Pure API versions 5.16.x - 5.17.x.

## Requirements and Recommendations

### Python Versions

pureapi requires Python >= 3.

### Pure API Domain and Key

The only configuration values the user absolutely must provide are a Pure API
domain and key. There are a couple of ways to do this:
* `client.Config` object
* `PURE_API_DOMAIN` and `PURE_API_KEY` environment variables

Running `pytest --integration tests/test_client.py` requires the environment
variables. One to set them is with a `.env` file. See `env.dist` for an example.

### pyenv, venv, and poetry

To install and manage Python versions we use [pyenv](https://github.com/pyenv/pyenv), and to manage
dependencies we use [poetry](https://poetry.eustace.io/). While alternative tools will work, we document
here only the tools we use. We will document the use of other tools if demand arises.

One way to set up all these tools to work together, for a new project, is to follow the workflow below.
Note that we prefer to put virtual environments inside the project directory. Note also that we use the
built-in `venv` module to create virtual environments, and we name their directories `.venv`, because
that is what `poetry` does and expects.

* Install pyenv.
* `pyenv install $python_version`
* `mkdir $project_dir; cd $project_dir`
* Create a `.python-version` file, containing `$python_version`.
* `pip install poetry`
* `poetry config settings.virtualenvs.in-project true`
* `python -m venv ./.venv/`
* `source ./.venv/bin/activate`

Now running commands like `poetry install` or `poetry update` should install packages into the virtual
environment in `./.venv`. Don't forget to `deactivate` the virtual environment when finished using it.
If the project virtual environment is not activated, `poetry run` and `poetry shell` will activate it.
When using `poetry shell`, exit the shell to deactivate the virtual environment.

## Installing

Add to `pyproject.toml`:

```
pureapi = {git = "git://github.com/UMNLibraries/pureapi.git"}
```

To specify a version, include the `tag` parameter:

```
pureapi = {git = "git://github.com/UMNLibraries/pureapi.git", tag = "1.0.0"}
```

To install, run `poetry install`.

## Testing

Run the following, either as arguments
to `poetry run`, or after running `poetry shell`:

```
pytest tests/test_client.py
pytest tests/test_common.py
pytest tests/test_response.py
```

Or to run all tests: `pytest`

Note that `tests/test_client.py` includes integration tests that make requests
against a Pure API server. To run those tests, pass the `--integration` option
to pytest, and set the environment variables described in
[Requirements and Recommendations](#requirements-and-recommendations).

## Contributing

### Include an updated `setup.py`.

Python package managers, including poetry, will be unable to install a VCS-based package without a
`setup.py` file in the project root. To generate `setup.py`:

```
poetry build
tar -zxf dist/pureapi-1.0.0.tar.gz pureapi-1.0.0/setup.py --strip-components 1
```

### Do not commit `pyproject.lock`.

To allow for flexibility in dependency versions, do _not_ commit `pyproject.lock`.
If multiple developers encounter problems with conflicting dependency versions, we may
consider committing `pyproject.lock` at that point.

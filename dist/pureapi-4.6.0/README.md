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
    config=Config(domain='test.example.com', key='456-def', version='523')
)
```

All functions that make requests of a Pure API server accept a `config`
parameter. See the documentation for `client.Config` for more details.

When using more than one function that requires configuration, or
calling such functions multiple times, `preconfig()` helps avoid
repetition, allowing multiple functions to be configured only once,
then re-used multiple times:

```python
# Pre-configure a single function:
[preconfigured_get] = client.preconfig(Config(version='523'), client.get)

# Another way to configure a single function:
preconfigured_get_all = client.preconfig(Config(version='523'), client.get_all)[0]

# Preconfigure multiple functions:
get, get_all, get_all_transformed = client.preconfig(
    Config(version='523'),
    client.get,
    client.get_all,
    client.get_all_transformed
) 
```

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

Successfully tested against Pure API versions 5.18.x - 5.21.x.

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

To manage dependencies we use [poetry](https://python-poetry.org/), and to manage Python versions
we use [pyenv](https://github.com/pyenv/pyenv). Some of us also use [anyenv](https://github.com/anyenv/anyenv)
to manage pyenv as well as other language version managers. While alternative tools will work, we document
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

### Deprecated Dependency Specification (versions <= 4.3.2)

Poetry seems to no longer reliably support git-repository-based dependencies.
While this method of specifying a dependency may still work for versions <= 4.3.1,
we recommended using the preferred method, with versions >= 4.3.2, below.

Add to `pyproject.toml`:

```
pureapi = {git = "https://github.com/UMNLibraries/pureapi.git"}
```

To specify a version, include the `tag` parameter:

```
pureapi = {git = "https://github.com/UMNLibraries/pureapi.git", tag = "4.3.2"}
```

### Preferred Dependency Specification (versions >= 4.3.3)

Add to `pyproject.toml` a URL-based dependency, with a path to a `tar.gz` file
in this repository's `dist/' directory:

```
pureapi = {url = "https://github.com/UMNLibraries/pureapi/raw/main/dist/pureapi-4.3.3.tar.gz"}
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

### Updating Supported Pure API Versions

Elsevier releases a new version of Pure, including a new version of the Pure API,
every four months.

### Testing Strategy and Tactics

Testing existing clients against new Pure API schema versions presents significant
challenges. Elsevier releases new versions of the Pure API every four months, and
supports only three versions older than the current version. Also, the JSON schema
for each API version is quite large, such that attempting to load them in some
schema browsers will cause them to crash. Much of this size is due to documentation,
which tends to change significantly between versions, making it difficult to find
the signal of actual schema changes when diffing schema versions against each other.

Our strategy for solving these problems is to test against only the fraction of
an API schema that we actually use, ignoring changes to parts of that schema we
do not use. The tactics we use here are to find sample records that contain all
of the fields we use for a given record type, and to run automated tests against
downloads of the same record from each supported API version endpoint. The sample
records are in [tests/data/](tests/data/), and the tests are in
[tests/test_response.py](tests/test_response.py).

### Google-Style Docstrings

We use [Google-style docstrings](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings).
The [Napoleon extension for Sphinx](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html)
has some [good examples](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html#example-google).

### Building - Deprecated Method (versions <= 4.3.2)

Poetry seems to no longer reliably support git-repository-based dependencies. Below is
a method of building packages we used previously for such dependencies.

#### Include an updated `setup.py`.

Python package managers, including poetry, will be unable to install a VCS-based package without a
`setup.py` file in the project root. To generate `setup.py`:

```
poetry build
tar -zxf dist/pureapi-1.0.0.tar.gz pureapi-1.0.0/setup.py --strip-components 1
```

### Building - Preferred Method (versions >= 4.3.3)

When specifying a dependency on this package, use a URL to a `tar.gz` file produced by
the following, as described in [Installing](#installing).

```
poetry build
```

### Do not commit `poetry.lock`.

To allow for flexibility in dependency versions, do _not_ commit `poetry.lock`.
If multiple developers encounter problems with conflicting dependency versions, we may
consider committing `pyproject.lock` at that point.

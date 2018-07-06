# pureapi

Tools for working with Elsevier's Pure API.

## Usage

Please see `tests/test_*.py` for now. We freely admit this section of the documentation requires
much improvement.

## Versions

Successfully tested against Pure API versions 5.10.x - 5.12.x.

## Installing

### Requirements and Recommendations

pureapi requires Python 3.

To install and manage Python versions and dependencies, we use
[pyenv](https://github.com/pyenv/pyenv) and [pipenv](https://docs.pipenv.org/). While using
multiple other tools should work, here we document the tools we use, which are most likely
to work.

To connect to the Pure server, including when running `tests/test_client.py`, the
`PURE_API_URL` and `PURE_API_KEY` environment variables must be set. See `env.dist` for
an example.

### Installing as an Application Dependency

Add to the application `Pipfile`:

```
pureapi = {git = "git://github.com/UMNLibraries/pureapi.git", editable = true}
```

### Installing as a Package/Library Dependency

Add to the package/library `setup.py`:

```
install_requires=[
  'pureapi',
],
dependency_links=[
  'git+https://github.com/UMNLibraries/pureapi.git#egg=pureapi',
],
``` 

### Installing for Development

Clone this repo, then run in the repo directory:

```
pipenv install -e '.[dev]'
```

That should install all dependencies, including dev dependencies, create a `Pipfile` with contents similar to...

```
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
pureapi = {editable = true, path = ".", extras = ["dev"]}

[dev-packages]

[requires]
python_version = "3.6"

```

...and put the dependency versions and/or hashes in `Pipfile.lock`.

Do _not_ commit `Pipfile` and `Pipfile.lock`! Those files are used only for local development, and
may cause breakage when installing pureapi as an application dependency. We use `setup.py` for that.

## Testing

After [installing for development](#installing-for-development), run the following, either as arguments to `pipenv run`, or after running `pipenv shell`:

```
pytest tests/test_client.py
pytest tests/test_response.py
```

Or to run all tests: `pytest`

Note that `tests/test_client.py` includes integration tests that make requests against a Pure server,
so the environment variables described in
[Requirements and Recommendations](#requirements-and-recommendations)
must be set in order to run those tests.

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

To install and manage Python versions we use [pyenv](https://github.com/pyenv/pyenv) and to manage
dependencies we use [poetry](https://poetry.eustace.io/). For now, poetry is required. We may consider
adding support for other dependency management tools if there is considerable demand for them.

To connect to the Pure server, including when running `tests/test_client.py`, the
`PURE_API_URL` and `PURE_API_KEY` environment variables must be set. See `env.dist` for
an example.

### Installing as a Dependency

Add to `pyproject.toml`:

```
pureapi = {git = "git://github.com/UMNLibraries/pureapi.git", tag = "1.0.0"}
```

### Installing for Development

Clone this repo, but do _not_ commit `pyproject.lock`!

## Testing

After [installing for development](#installing-for-development), run the following, either as arguments
to `poetry run`, or after running `poetry shell`:

```
pytest tests/test_client.py
pytest tests/test_response.py
```

Or to run all tests: `pytest`

Note that `tests/test_client.py` includes integration tests that make requests against a Pure server,
so the environment variables described in
[Requirements and Recommendations](#requirements-and-recommendations)
must be set in order to run those tests.

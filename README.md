# pureapi

Tools for working with Elsevier's Pure API.

## Usage

Please see `tests/test_*.py` for now. We freely admit this section of the documentation requires
much improvement.

## Pure API Versions

Successfully tested against Pure API versions 5.10.x - 5.12.x.

## Requirements and Recommendations

pureapi requires Python 3.

To install and manage Python versions we use [pyenv](https://github.com/pyenv/pyenv) and to manage
dependencies we use [poetry](https://poetry.eustace.io/). For now, poetry is required. We may consider
adding support for other dependency management tools if there is considerable demand for them.

To connect to the Pure server, including when running `tests/test_client.py`, the
`PURE_API_URL` and `PURE_API_KEY` environment variables must be set. One option is to set them in a 
`.env` file. See `env.dist` for an example.

## Installing

Add to `pyproject.toml`:

```
pureapi = {git = "git://github.com/UMNLibraries/pureapi.git"}
```

To specify a version, include the `tag` parameter:

```
pureapi = {git = "git://github.com/UMNLibraries/pureapi.git", tag = "1.0.0"}
```

## Testing

Run the following, either as arguments
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



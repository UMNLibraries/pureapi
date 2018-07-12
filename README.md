# pureapi

Tools for working with Elsevier's Pure API.

## Usage

Please see `tests/test_*.py` for now. We freely admit this section of the documentation requires
much improvement.

## Pure API Versions

Successfully tested against Pure API versions 5.10.x - 5.12.x.

## Requirements and Recommendations

### Python Versions

pureapi requires Python >= 3.

### Environment Variables

To connect to the Pure server, including when running `tests/test_client.py`, the
`PURE_API_URL` and `PURE_API_KEY` environment variables must be set. One option is to set them in a 
`.env` file. See `env.dist` for an example.

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



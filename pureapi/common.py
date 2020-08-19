import functools
import json
import os
import pathlib
from typing import Any, Callable, MutableMapping, Tuple, TypeVar, cast

from pureapi.exceptions import PureAPIException

schemas_path = pathlib.Path(__file__).parent.parent / 'schemas'

# The commented out version seems more elegant, but using map() and filter() as an
# exercise in functional programming in Python.
#versions = tuple((item.name for item in os.scandir(schemas_path) if item.is_dir()))
versions = tuple(
    map(lambda item: item.name,
        filter(lambda item: item.name if item.is_dir() else None, os.scandir(schemas_path))
    )
)

def valid_version(version: str) -> bool:
    return (version in versions)

latest_version = str(max([int(version) for version in versions]))
oldest_version = str(min([int(version) for version in versions]))
env_version_varname = 'PURE_API_VERSION'
def env_version() -> str:
    return os.environ.get(env_version_varname)

def default_version() -> str:
    return env_version() if env_version() is not None else latest_version

class PureAPIMissingVersionError(ValueError, PureAPIException):
    def __init__(self, *args, **kwargs):
        super().__init__(f'No version found in kwargs, default_version, or {env_version_varname}', *args, **kwargs)

class PureAPIInvalidVersionError(ValueError, PureAPIException):
    def __init__(self, version, *args, **kwargs):
        super().__init__(f'Invalid version "{version}"', *args, **kwargs)

F = TypeVar('F', bound=Callable[..., Any])

def validate_version(func: F) -> F:
    @functools.wraps(func)
    def wrapper_validate_version(*args, **kwargs):
        if 'version' in kwargs and kwargs['version'] is not None:
            if not valid_version(kwargs['version']):
                raise PureAPIInvalidVersionError(kwargs['version'])
        else:
            kwargs['version'] = None
        if kwargs['version'] is None and default_version() is not None:
            if valid_version(default_version()):
                kwargs['version'] = default_version()
            else:
                raise PureAPIInvalidVersionError(default_version())
        if kwargs['version'] is None:
            raise PureAPIMissingVersionError()
        return func(*args, **kwargs)
    return cast(F, wrapper_validate_version)

def schema_516() -> MutableMapping:
    with open(schemas_path  / '516/swagger.json') as json_file:
        return json.load(json_file)

def schema_517() -> MutableMapping:
    with open(schemas_path  / '517/swagger.json') as json_file:
        return json.load(json_file)

@functools.lru_cache(maxsize=None)
@validate_version
def schema_for(*, version: str = None) -> MutableMapping:
    return globals()[f'schema_{version}']()

def collections_516() -> Tuple[str]:
    return tuple(map(lambda tag: tag['name'], schema_for(version='516')['tags']))

def collections_517() -> Tuple[str]:
    return tuple(map(lambda tag: tag['name'], schema_for(version='517')['tags']))

@functools.lru_cache(maxsize=None)
@validate_version
def collections_for(*, version: str) -> Tuple[str]:
    return globals()[f'collections_{version}']()

@validate_version
def valid_collection(*, collection: str, version: str = None) -> bool:
    return (collection in collections_for(version=version))

class PureAPIInvalidCollectionError(ValueError, PureAPIException):
    def __init__(self, *args, collection, version, **kwargs):
        super().__init__(f'Invalid collection "{collection}" for version "{version}"', *args, **kwargs)

def validate_collection(func: F) -> F:
    @functools.wraps(func)
    @validate_version
    def wrapper_validate_collection(*args, **kwargs):
        if not valid_collection(collection=kwargs['collection'], version=kwargs['version']):
            raise PureAPIInvalidCollectionError(collection=kwargs['collection'], version=kwargs['version'])
        return func(*args, **kwargs)
    return cast(F, wrapper_validate_collection)


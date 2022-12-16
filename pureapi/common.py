import functools
import json
import os
from pathlib import Path
from typing import Any, Callable, MutableMapping, Tuple, TypeVar, cast

from pureapi.exceptions import PureAPIException

schemas_path: Path = Path(__file__).parent / 'schemas'
'''Parent path of swagger.io/json schema files for Pure API versions. Child
directories are named for versions, without the periods, e.g., ``518`` for
version 5.17.'''

# The commented out version seems more elegant, but using map() and filter() as an
# exercise in functional programming in Python.
#versions = tuple((item.name for item in os.scandir(schemas_path) if item.is_dir()))
versions: Tuple[str] = tuple(
    map(lambda item: item.name,
        filter(lambda item: item.name if item.is_dir() else None, os.scandir(schemas_path))
    )
)
'''All Pure API versions this package recognizes and supports.'''

def valid_version(version: str) -> bool:
    '''For the given ``version``, returns ``True`` or ``False`` according to its
    validity.'''
    return (version in versions)

latest_version: str = str(max([int(version) for version in versions]))
'''Latest valid Pure API version.'''

oldest_version: str = str(min([int(version) for version in versions]))
'''Oldest valid Pure API version.'''

env_version_varname: str = 'PURE_API_VERSION'
'''Environment variable name for a Pure API version. Defaults to
PURE_API_VERSION.  Used by ``env_version()``.
'''

def env_version() -> str:
    '''Returns the value of environment variable ``env_version_varname``, or
    None if undefined.'''
    return os.environ.get(env_version_varname)

def default_version() -> str:
    '''Returns the value of environment variable ``env_version_varname``, or
    ``latest_version`` if the environment variable is undefined.'''
    return env_version() if env_version() is not None else latest_version

class PureAPIMissingVersionError(ValueError, PureAPIException):
    '''Raised when a Pure API version is expected but missing.'''
    def __init__(self, *args, **kwargs):
        super().__init__(f'No version found in kwargs, default_version, or {env_version_varname}', *args, **kwargs)

class PureAPIInvalidVersionError(ValueError, PureAPIException):
    '''Raised when a Pure API version is unrecognized.'''
    def __init__(self, version, *args, **kwargs):
        super().__init__(f'Invalid version "{version}"', *args, **kwargs)

F = TypeVar('F', bound=Callable[..., Any])

def validate_version(func: F) -> F:
    '''A decorator wrapper that validates a kwarg Pure API version.

    Args:
        func: The function to be wrapped.

    Return:
        The wrapped function.

    Raises:
        PureAPIMissingVersionError: If the ``version`` kwarg is missing or
            the value is None.
        PureAPIInvalidVersionError: If the ``version`` is unrecognized.
    '''
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

def schema_524() -> MutableMapping:
    '''Returns a mapping representation of the Pure API version 5.24 schema.'''
    with open(schemas_path  / '524/swagger.json') as json_file:
        return json.load(json_file)

def schema_523() -> MutableMapping:
    '''Returns a mapping representation of the Pure API version 5.23 schema.'''
    with open(schemas_path  / '523/swagger.json') as json_file:
        return json.load(json_file)

def schema_522() -> MutableMapping:
    '''Returns a mapping representation of the Pure API version 5.22 schema.'''
    with open(schemas_path  / '522/swagger.json') as json_file:
        return json.load(json_file)

def schema_521() -> MutableMapping:
    '''Returns a mapping representation of the Pure API version 5.21 schema.'''
    with open(schemas_path  / '521/swagger.json') as json_file:
        return json.load(json_file)

def schema_520() -> MutableMapping:
    '''Returns a mapping representation of the Pure API version 5.20 schema.'''
    with open(schemas_path  / '520/swagger.json') as json_file:
        return json.load(json_file)

@functools.lru_cache(maxsize=None)
@validate_version
def schema_for(*, version: str = None) -> MutableMapping:
    '''Returns a mapping representation of the schema for the given Pure API
    ``version``.'''
    return globals()[f'schema_{version}']()

def collections_524() -> Tuple[str]:
    '''Returns a tuple of all collection names in the Pure API version 5.24
    schema.'''
    return tuple(map(lambda tag: tag['name'], schema_for(version='524')['tags']))

def collections_523() -> Tuple[str]:
    '''Returns a tuple of all collection names in the Pure API version 5.23
    schema.'''
    return tuple(map(lambda tag: tag['name'], schema_for(version='523')['tags']))

def collections_522() -> Tuple[str]:
    '''Returns a tuple of all collection names in the Pure API version 5.22
    schema.'''
    return tuple(map(lambda tag: tag['name'], schema_for(version='522')['tags']))

def collections_521() -> Tuple[str]:
    '''Returns a tuple of all collection names in the Pure API version 5.21
    schema.'''
    return tuple(map(lambda tag: tag['name'], schema_for(version='521')['tags']))

def collections_520() -> Tuple[str]:
    '''Returns a tuple of all collection names in the Pure API version 5.20
    schema.'''
    return tuple(map(lambda tag: tag['name'], schema_for(version='520')['tags']))

@functools.lru_cache(maxsize=None)
@validate_version
def collections_for(*, version: str) -> Tuple[str]:
    '''Returns a tuple of all collection names in the schema for the given Pure
    API ``version``.'''
    return globals()[f'collections_{version}']()

@validate_version
def valid_collection(*, collection: str, version: str = None) -> bool:
    '''For the given ``collection``, returns ``True`` or ``False`` according to whether
    or not it is valid for the given ``version``.'''
    return (collection in collections_for(version=version))

class PureAPIInvalidCollectionError(ValueError, PureAPIException):
    '''Raised when the given ``collection`` name is invalid for the given Pure
    API ``version``.'''
    def __init__(self, *args, collection, version, **kwargs):
        super().__init__(f'Invalid collection "{collection}" for version "{version}"', *args, **kwargs)

def validate_collection(func: F) -> F:
    '''A decorator wrapper that validates a kwarg Pure API ``collection`` for a
    kwarg ``version``.

    Args:
        func: The function to be wrapped.

    Return:
        The wrapped function.

    Raises:
        PureAPIInvalidCollectionError: If the given ``collection`` is invalid
        for the ``version``.
    '''
    @functools.wraps(func)
    @validate_version
    def wrapper_validate_collection(*args, **kwargs):
        if not valid_collection(collection=kwargs['collection'], version=kwargs['version']):
            raise PureAPIInvalidCollectionError(collection=kwargs['collection'], version=kwargs['version'])
        return func(*args, **kwargs)
    return cast(F, wrapper_validate_collection)

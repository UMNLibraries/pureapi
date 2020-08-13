import functools
import json
import os
import pathlib

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

def valid_version(version):
    return (version in versions)

latest_version = str(max([int(version) for version in versions]))
oldest_version = str(min([int(version) for version in versions]))
env_version_varname = 'PURE_API_VERSION'
def env_version():
    return os.environ.get(env_version_varname)

def default_version():
    return env_version() if env_version() is not None else latest_version

class PureAPIMissingVersionError(ValueError, PureAPIException):
    def __init__(self, *args, **kwargs):
        super().__init__(f'No version found in kwargs, default_version, or {env_version_varname}', *args, **kwargs)

class PureAPIInvalidVersionError(ValueError, PureAPIException):
    def __init__(self, *args, version, version_varname, **kwargs):
        super().__init__(f'Invalid version "{version}" in {version_varname}', *args, **kwargs)

def validate_version(func):
    @functools.wraps(func)
    def wrapper_validate_version(*args, **kwargs):
        if 'version' in kwargs and kwargs['version'] is not None:
            if not valid_version(kwargs['version']):
                raise PureAPIInvalidVersionError(
                    version=kwargs['version'],
                    version_varname="kwargs['version']"
                )
        else:
            kwargs['version'] = None
        if kwargs['version'] is None and default_version is not None:
            if valid_version(default_version):
                kwargs['version'] = default_version
            else:
                raise PureAPIInvalidVersionError(
                    version=default_version,
                    version_varname='default_version'
                )
        if kwargs['version'] is None and env_version() is not None:
            if valid_version(env_version()):
                kwargs['version'] = env_version()
            else:
                raise PureAPIInvalidVersionError(
                    version=env_version(),
                    version_varname=env_version_varname
                )
        if kwargs['version'] is None:
            raise PureAPIMissingVersionError()
        return func(*args, **kwargs)
    return wrapper_validate_version

def schema_516():
    with open(schemas_path  / '516/swagger.json') as json_file:
        return json.load(json_file)

def schema_517():
    with open(schemas_path  / '517/swagger.json') as json_file:
        return json.load(json_file)

@functools.lru_cache(maxsize=None)
@validate_version
def schema_for(*, version=None):
    return globals()[f'schema_{version}']()

def collections_516():
    return tuple(map(lambda tag: tag['name'], schema_for(version='516')['tags']))

def collections_517():
    return tuple(map(lambda tag: tag['name'], schema_for(version='517')['tags']))

@functools.lru_cache(maxsize=None)
@validate_version
def collections_for(*, version):
    return globals()[f'collections_{version}']()

@validate_version
def valid_collection(*, collection, version=None):
    return (collection in collections_for(version=version))

class PureAPIInvalidCollectionError(ValueError, PureAPIException):
    def __init__(self, *args, collection, version, **kwargs):
        super().__init__(f'Invalid collection "{collection}" for version "{version}"', *args, **kwargs)

def validate_collection(func):
    @functools.wraps(func)
    @validate_version
    def wrapper_validate_collection(*args, **kwargs):
        if not valid_collection(collection=kwargs['collection'], version=kwargs['version']):
            raise PureAPIInvalidCollectionError(collection=kwargs['collection'], version=kwargs['version'])
        return func(*args, **kwargs)
    return wrapper_validate_collection


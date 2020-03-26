import functools
import json
import os
import pathlib
from .exceptions import PureAPIInvalidVersionError, PureAPIInvalidCollectionError

default_version = os.environ.get('PURE_API_VERSION')
default_base_url = os.environ.get('PURE_API_BASE_URL')

# Keep the following just for backward compatibility, or what?
default_url = os.environ.get('PURE_API_URL')

default_key = os.environ.get('PURE_API_KEY')

schemas_path = pathlib.Path(__file__).parent.parent / 'schemas'
versions = [item.name for item in os.scandir(schemas_path) if item.is_dir()]

def valid_version(version):
    return (version in versions)

def validate_version(func):
    @functools.wraps(func)
    def wrapper_validate_version(*args, **kwargs):
        if 'version' not in kwargs:
            kwargs['version'] = default_version
        if not valid_version(kwargs['version']):
            raise PureAPIInvalidVersionError(version=kwargs['version'])
        value = func(*args, **kwargs)
        return value
    return wrapper_validate_version

@validate_version
def url(*, base_url=None, version=None):
    base_url = default_base_url if base_url is None else base_url
    return f'{default_base_url}/{version}/'

def schema_516():
    with open(schemas_path  / '516/swagger.json') as json_file:
        return json.load(json_file)

def schema_517():
    with open(schemas_path  / '517/swagger.json') as json_file:
        return json.load(json_file)

@functools.lru_cache(maxsize=None)
@validate_version
def schema(*, version=None):
    return globals()[f'schema_{version}']()

def collections_516():
    return [collection['name'] for collection in schema(version='516')['tags']]

def collections_517():
    return [collection['name'] for collection in schema(version='517')['tags']]

@functools.lru_cache(maxsize=None)
@validate_version
def collections(*, version):
    return globals()[f'collections_{version}']()

@validate_version
def valid_collection(*, collection, version=None):
    return (collection in collections(version=version))

def validate_collection(func):
    @functools.wraps(func)
    def wrapper_validate_collection(*args, **kwargs):
        if not valid_collection(collection=kwargs['collection'], version=kwargs['version']):
            raise PureAPIInvalidCollectionError(collection=kwargs['collection'], version=kwargs['version'])
        value = func(*args, **kwargs)
        return value
    return wrapper_validate_collection


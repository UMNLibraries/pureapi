import functools
import json
import os
import pathlib

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
            raise ValueError
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

def endpoints_516():
    return [endpoint['name'] for endpoint in schema(version='516')['tags']]

def endpoints_517():
    return [endpoint['name'] for endpoint in schema(version='517')['tags']]

@functools.lru_cache(maxsize=None)
@validate_version
def endpoints(*, version):
    return globals()[f'endpoints_{version}']()

@validate_version
def valid_endpoint(*, endpoint, version=None):
    return (endpoint in endpoints(version=version))

def validate_endpoint(func):
    @functools.wraps(func)
    def wrapper_validate_endpoint(*args, **kwargs):
        if not valid_endpoint(endpoint=kwargs['endpoint'], version=kwargs['version']):
            raise ValueError
        value = func(*args, **kwargs)
        return value
    return wrapper_validate_endpoint


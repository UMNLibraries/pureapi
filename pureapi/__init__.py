import functools
import json
import os
import pathlib
from .exceptions import PureAPIInvalidVersionError, PureAPIInvalidCollectionError, PureAPIMissingDomainError

default_key = os.environ.get('PURE_API_KEY')

schemas_path = pathlib.Path(__file__).parent.parent / 'schemas'

# The commented out version seems more elegant, but using map() and filter() as an
# exercise in functional programming in Python.
#versions = tuple((item.name for item in os.scandir(schemas_path) if item.is_dir()))
versions = tuple(
    map(lambda item: item.name,
        filter(lambda item: item.name if item.is_dir() else None, os.scandir(schemas_path))
    )
)

latest_version = str(max([int(version) for version in versions]))

def valid_version(version):
    return (version in versions)

def _find_default_version():
    env_version = os.environ.get('PURE_API_VERSION')
    if env_version is not None:
        if valid_version(env_version):
            return env_version
        else:
            raise PureAPIInvalidVersionError(
                version=env_version,
                extra_message='in PURE_API_VERSION'
            )
    else:
        return latest_version
default_version = _find_default_version()

def validate_version(func):
    @functools.wraps(func)
    def wrapper_validate_version(*args, **kwargs):
        if 'version' not in kwargs:
            kwargs['version'] = default_version
        if not valid_version(kwargs['version']):
            raise PureAPIInvalidVersionError(version=kwargs['version'])
        return func(*args, **kwargs)
    return wrapper_validate_version

# Deprecate this:
default_url = os.environ.get('PURE_API_URL')

default_domain = os.environ.get('PURE_API_DOMAIN')
default_protocol = 'https'
default_path = 'ws/api'

@functools.lru_cache(maxsize=None)
@validate_version
def construct_base_url(*, protocol=None, domain=None, path=None, version=None):
    url_domain = domain if domain is not None else default_domain
    if url_domain is None:
        raise PureAPIMissingDomainError('No domain passed in args and PURE_API_DOMAIN is undefined')
    url_protocol = protocol if protocol is not None else default_protocol
    url_path = path if path is not None else default_path
    return f'{url_protocol}://{url_domain}/{url_path}/{version}/'

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
    return tuple(map(lambda tag: tag['name'], schema(version='516')['tags']))

def collections_517():
    return tuple(map(lambda tag: tag['name'], schema(version='517')['tags']))

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
        return func(*args, **kwargs)
    return wrapper_validate_collection


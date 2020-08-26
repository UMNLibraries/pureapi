import math
import os
from typing import Callable, Iterator, List, Mapping, MutableMapping

import addict
import attr
import requests
from requests.exceptions import RequestException, HTTPError
from tenacity import Retrying, wait_exponential

from pureapi import response
from pureapi.common import default_version, valid_collection, valid_version, PureAPIInvalidCollectionError, PureAPIInvalidVersionError
from pureapi.exceptions import PureAPIException

env_key_varname: str = 'PURE_API_KEY'
'''Environment variable name for a Pure API key. Defaults to PURE_API_KEY.
Used by env_key().
'''

def env_key() -> str:
    '''Returns the value of environment variable env_key_varname, or None if undefined.
    See Config for more details.
    '''
    return os.environ.get(env_key_varname)

def default_protocol() -> str:
    '''Returns 'https'. See Config for more details.'''
    return 'https'

def default_base_path() -> str:
    '''Returns 'ws/api'. See Config for more details.'''
    return 'ws/api'

def default_headers() -> MutableMapping:
    '''See Config for more details.

    Returns:
        {
            'Accept': 'application/json',
            'Accept-Charset': 'utf-8',
        }
    '''
    return {
        'Accept': 'application/json',
        'Accept-Charset': 'utf-8',
    }

def default_retryer() -> Callable:
    '''A function that retries HTTP requests to the Pure API server.

    Returns:
        Retrying(wait=wait_exponential(multiplier=1, max=60), reraise=True)
    '''
    return Retrying(wait=wait_exponential(multiplier=1, max=60), reraise=True)

class PureAPIClientException(PureAPIException):
    '''Base class for exceptions specific to pureapi.client.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

env_domain_varname: str = 'PURE_API_DOMAIN'
'''Environment variable name for a Pure API domain. Defaults to PURE_API_DOMAIN.
Used by env_domain().
'''

def env_domain() -> str:
    '''Returns the value of environment variable env_domain_varname, or None if undefined.
    See Config for more details.
    '''
    return os.environ.get(env_domain_varname)

def _get_collection_from_resource_path(resource_path: str, version: str) -> str:
    '''Extracts the collection name from a Pure API URL resource path.

    Args:
        resource_path: URL path, without the base URL, to a Pure API resource.
        config: Instance of pureapi.client.Config.

    Returns:
        The name of the collection.

    Raises:
        common.PureAPIInvalidCollectionError: If the extracted collection is
            invalid for the given API version.
    '''
    collection = resource_path.split('/')[0]
    if not valid_collection(collection=collection, version=version):
        raise PureAPIInvalidCollectionError(collection=collection, version=version)
    return collection

class PureAPIHTTPError(HTTPError, PureAPIClientException):
    '''Raised in case of an HTTP error response.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PureAPIRequestException(RequestException, PureAPIClientException):
    '''Raised in case of an HTTP-request-related exception that is something
    other than an HTTP error status code.'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@attr.s(auto_attribs=True, frozen=True)
class Config:
    '''Common client configuration settings. Used by most functions.

    Most attributes have defaults and are not required. Only ``domain`` and
    ``key`` are required, and both can be set with environment variables as
    well as constructor parameters.

    Config instances are immutable. To use different configurations for different
    function calls, pass different Config objects.

    Examples:
        >>> from pureapi import client
        >>> client.Config(domain='example.com', key='123-abc')
        Config(protocol='https', domain='example.com', base_path='ws/api', version='517', key='123-abc', headers={'Accept': 'application/json', 'Accept-Charset': 'utf-8', 'api-key': '123-abc'}, retryer=<Retrying object at 0x7fec3af4c278 (stop=<tenacity.stop._stop_never object at 0x7fec34a76908>, wait=<tenacity.wait.wait_exponential object at 0x7fec3af4c208>, sleep=<built-in function sleep>, retry=<tenacity.retry.retry_if_exception_type object at 0x7fec34a82ba8>, before=<function before_nothing at 0x7fec34a6d950>, after=<function after_nothing at 0x7fec34a85378>)>, base_url='https://example.com/ws/api/517/')

        >>> client.Config(domain='test.example.com', key='456-def', version='516')
        Config(protocol='https', domain='test.example.com', base_path='ws/api', version='516', key='456-def', headers={'Accept': 'application/json', 'Accept-Charset': 'utf-8', 'api-key': '456-def'}, retryer=<Retrying object at 0x7fec3454d828 (stop=<tenacity.stop._stop_never object at 0x7fec34a76908>, wait=<tenacity.wait.wait_exponential object at 0x7fec3454d860>, sleep=<built-in function sleep>, retry=<tenacity.retry.retry_if_exception_type object at 0x7fec34a82ba8>, before=<function before_nothing at 0x7fec34a6d950>, after=<function after_nothing at 0x7fec34a85378>)>, base_url='https://test.example.com/ws/api/516/')
    '''

    protocol: str = attr.ib(
        factory=default_protocol,
        validator=[
            attr.validators.instance_of(str),
            attr.validators.in_(['http','https']),
        ]
    )
    '''HTTP protocol. Must be either ``https`` or ``http``. Default: ``https``'''

    domain: str = attr.ib(
        factory=env_domain,
        validator=attr.validators.instance_of(str)
    )
    '''Domain of a Pure API server. Required. Default: Return value of ``env_domain()``.'''

    base_path: str = attr.ib(
        factory=default_base_path,
        validator=[
            attr.validators.instance_of(str),
        ]
    )
    '''Base path of the Pure API URL entry point, without the version number segment.
    Default: Return value of ``default_base_path()``.'''

    version: str = attr.ib(
        factory=default_version,
        validator=attr.validators.instance_of(str)
    )
    '''Pure API version, without the decimal point. For example, ``517`` for version 5.17.
    Default: Return value of ``default_version()``.'''
    @version.validator
    def validate_version(self, attribute: str, value: str) -> None:
        if not valid_version(value):
            raise PureAPIInvalidVersionError(value)

    key: str = attr.ib(
        factory=env_key,
        validator=attr.validators.instance_of(str)
    )
    '''Pure API key. Required. Default: Return value of ``env_key()``.'''

    headers: MutableMapping = attr.ib(
        factory=default_headers,
        validator=attr.validators.instance_of(MutableMapping)
    )
    '''HTTP headers. Default: Return value of ``default_headers()``. The
    constructor automatically adds an ``api-key`` header, using the value of
    the ``key`` attribute.'''

    retryer: Callable = attr.ib(
        factory=default_retryer,
        validator=attr.validators.is_callable()
    )
    '''A function that retries HTTP requests to the Pure API server. Must have
    inputs and outputs interchangeable with those of ``tenacity.Retrying()``.
    Default: Return value of ``default_retryer()``.'''

    base_url: str = attr.ib(init=False)
    '''Pure API entrypoint URL. Should not be included in constructor
    parameters. The constructor generates this automatically based on
    other attributes.'''

    def __attrs_post_init__(self) -> None:
        self.headers['api-key'] = self.key
        object.__setattr__(self, 'base_url', f'{self.protocol}://{self.domain}/{self.base_path}/{self.version}/')

def get(resource_path: str, params: Mapping = None, config: Config = None) -> requests.Response:
    '''Makes an HTTP GET request for Pure API resources.

    Note that many collections likely contain more resources than can be
    practically downloaded in a single request. To get all resources
    in a collection, see ``get_all()``.

    Args:
        resource_path: URL path to a Pure API resource, to be appended to the
            ``Config.base_url``. Do not include a leading forward slash (``/``).
        params: A mapping representing URL query string params. Default: ``{}``.
        config: An instance of Config. If not provided, this function attempts
            to automatically instantiate a Config based on environment variables
            and default values.

    Returns:
        An HTTP response object.

    Raises:
        common.PureAPIInvalidCollectionError: If the collection, the first
            segment in the resource_path, is invalid for the given API version.
        PureAPIHTTPError: If the response includes an HTTP error code, possibly
            after multiple retries.
        PureAPIRequestException: If the request generated some error unrelated
            to any HTTP error status.
        PureAPIClientException: Some unexpected exception that is none of the
            above.
    '''
    if params is None:
        params = {}

    if config is None:
        config = Config()

    collection = _get_collection_from_resource_path(resource_path, config.version)
    with requests.Session() as s:
        prepped = s.prepare_request(requests.Request('GET', config.base_url + resource_path, params=params))
        prepped.headers = {**prepped.headers, **config.headers}

        try:
            r = config.retryer(s.send, prepped)
            r.raise_for_status()
            return r
        except HTTPError as http_exc:
            raise PureAPIHTTPError(
                f'GET request for resource path {resource_path} with params {params} returned HTTP status {http_exc.response.status_code}',
                request=http_exc.request,
                response=http_exc.response
            ) from http_exc
        except RequestException as req_exc:
            raise PureAPIRequestException(
                f'Failed GET request for resource path {resource_path} with params {params}',
                request=req_exc.request,
                response=req_exc.response
            ) from req_exc
        except Exception as e:
            raise PureAPIClientException(
                f'Unexpected exception for GET request for resource path {resource_path} with params {params}'
            ) from e

def get_all(resource_path: str, params: Mapping = None, config: Config = None) -> Iterator[requests.Response]:
    '''Makes as many HTTP GET requests as necessary to get all resources in a
    collection, possibly restricted by the ``params``.

    Conveniently calculates the offset for each request, based on the desired
    number of records per request, as given by ``params['size']``.

    Args:
        resource_path: URL path to a Pure API resource, to be appended to the
            ``Config.base_url``. Do not include a leading forward slash (``/``).
        params: A mapping representing URL query string params. Default:
            ``{'size': 100}``
        config: An instance of Config. If not provided, this function attempts
            to automatically instantiate a Config based on environment variables
            and default values.

    Yields:
        HTTP response objects.

    Raises:
        common.PureAPIInvalidCollectionError: If the collection, the first
            segment in the resource_path, is invalid for the given API version.
        PureAPIHTTPError: If the response includes an HTTP error code, possibly
            after multiple retries.
        PureAPIRequestException: If the request generated some error unrelated
            to any HTTP error status.
        PureAPIClientException: Some unexpected exception that is none of the
            above.
    '''
    if params is None:
        params = {}

    if config is None:
        config = Config()

    count_params = {
        **params,
        'size': 0,
        'offset': 0,
    }
    r = get(resource_path, count_params, config)
    json = r.json()
    record_count = int(json['count'])
    window_size = int(params['size']) if 'size' in params else 100
    window_count = int(math.ceil(float(record_count) / window_size))

    for window in range(0, window_count):
        window_params = {
            **params,
            'offset': window * window_size,
            'size': window_size,
        }
        yield get(resource_path, window_params, config)

def get_all_transformed(
    resource_path: str,
    params: Mapping = None,
    config: Config = None
) -> Iterator[addict.Dict]:
    if params is None:
        params = {}

    if config is None:
        config = Config()

    collection = _get_collection_from_resource_path(resource_path, config.version)
    for r in get_all(resource_path, params, config):
        for item in r.json()['items']:
            yield response.transform(collection, item, version=config.version)

def get_all_changes(start_date: str, params: Mapping = None, config: Config = None) -> Iterator[requests.Response]:
    '''Makes as many HTTP GET requests as necessary to get all resources from
    the changes collection, from a start date forward.

    Conveniently finds resumption tokens and automatically adds them to each
    subsequent request.

    Args:
        start_date: Date in ISO 8601 format, YYYY-MM-DD.
        params: A mapping representing URL query string params. Default:
            ``{'size': 100}``
        config: An instance of Config. If not provided, this function attempts
            to automatically instantiate a Config based on environment variables
            and default values.

    Yields:
        HTTP response objects.

    Raises:
        common.PureAPIInvalidCollectionError: If the collection, the first
            segment in the resource_path, is invalid for the given API version.
        PureAPIHTTPError: If the response includes an HTTP error code, possibly
            after multiple retries.
        PureAPIRequestException: If the request generated some error unrelated
            to any HTTP error status.
        PureAPIClientException: Some unexpected exception that is none of the
            above.
    '''
    if params is None:
        params = {'size': 100}

    if config is None:
        config = Config()

    next_token_or_date = start_date
    while(True):
        r = get('changes/' + next_token_or_date, params, config)
        json = r.json()

        if json['moreChanges'] is True:
            next_token_or_date = str(json['resumptionToken'])
            if int(json['count']) == 0 or 'items' not in json:
                # We skip these responses, under the assumption that a caller wanting all changes will
                # have no use for a response that contains no changes.
                # The "count" in changes responses has different semantics from all other endpoints.
                # While for all others "count" is the total number of records that matched the request,
                # for changes it is the number of records in the current response. According to Elsevier,
                # "In an extreme scenario the count can be 0 while moreChanges is true, if for example
                # all 100 changes are on confidential content"
                # -- https://support.pure.elsevier.com/browse/PURESUPPORT-63657?focusedCommentId=560888&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-560888
                # We have seen counts of 0, sometimes in multiple, consecutive responses. When "count"
                # is zero, there will be no "items", so we check for that, too, for some extra protection.
                continue
        else:
            break

        yield r

def get_all_changes_transformed(
    start_date: str,
    params: Mapping = None,
    config: Config = None
) -> Iterator[addict.Dict]:
    if params is None:
        params = {}

    if config is None:
        config = Config()

    for r in get_all_changes(start_date, params, config):
        for item in r.json()['items']:
            yield response.transform('changes', item, version=config.version)

def filter(resource_path: str, payload: Mapping = None, config: Config = None) -> requests.Response:
    '''Makes an HTTP POST request for Pure API resources, filtered according to the payload.

    Note that many collections likely contain more resources than can be
    practically downloaded in a single request. To filter all resources
    in a collection, see ``filter_all()``.

    Args:
        resource_path: URL path to a Pure API resource, to be appended to the
            ``Config.base_url``. Do not include a leading forward slash (``/``).
        payload: A mapping representing JSON filters of the collection. Default: ``{}``.
        config: An instance of Config. If not provided, this function attempts
            to automatically instantiate a Config based on environment variables
            and default values.

    Returns:
        An HTTP response object.

    Raises:
        common.PureAPIInvalidCollectionError: If the collection, the first
            segment in the resource_path, is invalid for the given API version.
        PureAPIHTTPError: If the response includes an HTTP error code, possibly
            after multiple retries.
        PureAPIRequestException: If the request generated some error unrelated
            to any HTTP error status.
        PureAPIClientException: Some unexpected exception that is none of the
            above.
    '''
    if payload is None:
        payload = {}

    if config is None:
        config = Config()

    collection = _get_collection_from_resource_path(resource_path, config.version)
    with requests.Session() as s:
        prepped = s.prepare_request(requests.Request('POST', config.base_url + resource_path, json=payload))
        prepped.headers = {**prepped.headers, **config.headers}

        try:
            r = config.retryer(s.send, prepped)
            r.raise_for_status()
            return r
        except HTTPError as http_exc:
            raise PureAPIHTTPError(
                f'POST request for resource path {resource_path} with payload {payload} returned HTTP status {http_exc.response.status_code}',
                request=http_exc.request,
                response=http_exc.response
            ) from http_exc
        except RequestException as req_exc:
            raise PureAPIRequestException(
                f'Failed POST request for resource path {resource_path} with payload {payload}',
                request=req_exc.request,
                response=req_exc.response
            ) from req_exc
        except Exception as e:
            raise PureAPIClientException(
                f'Unexpected exception for POST request for resource path {resource_path} with payload {payload}'
            ) from e

def filter_all(resource_path: str, payload: Mapping = None, config: Config = None) -> Iterator[requests.Response]:
    if payload is None:
        payload = {}

    if config is None:
        config = Config()

    count_payload = {
        **payload,
        'size': 0,
        'offset': 0,
    }
    r = filter(resource_path, count_payload, config)
    json = r.json()
    record_count = int(json['count'])
    window_size = int(payload.setdefault('size', 100))
    if window_size <= 0:
        window_size = 100
    payload['size'] = window_size
    window_count = int(math.ceil(float(record_count) / window_size))

    for window in range(0, window_count):
        window_payload = {
            **payload,
            'offset': window * window_size,
        }
        yield filter(resource_path, window_payload, config)

def _group_items(items: List = None, items_per_group: int = 100) -> Iterator[List]:
    if items is None:
        items = []
    items_per_group = int(items_per_group)
    if items_per_group <= 0:
        items_per_group = default_items_per_group
    start = 0
    end = items_per_group
    while start < len(items):
        yield items[start:end]
        start += items_per_group
        end += items_per_group

def filter_all_by_uuid(
    resource_path: str,
    payload: Mapping = None,
    uuids: List = None,
    uuids_per_request: int = 100,
    config: Config = None
) -> Iterator[requests.Response]:
    if payload is None:
        payload = {}

    if uuids is None:
        uuids = []

    if config is None:
        config = Config()

    for uuid_group in _group_items(items=uuids, items_per_group=uuids_per_request):
        group_payload = {
            **payload,
            'uuids': uuid_group,
            'size': len(uuid_group),
        }
        yield filter(resource_path, group_payload, config)

def filter_all_by_id(
    resource_path: str,
    payload: Mapping = None,
    ids: List = None,
    ids_per_request: int = 100,
    config: Config = None
) -> Iterator[requests.Response]:
    if payload is None:
        payload = {}

    if ids is None:
        ids = []

    if config is None:
        config = Config()

    for id_group in _group_items(items=ids, items_per_group=ids_per_request):
        group_payload = {
            **payload,
            'ids': id_group,
            'size': len(id_group),
        }
        yield filter(resource_path, group_payload, config)

def filter_all_transformed(
    resource_path: str,
    payload: Mapping = None,
    config: Config = None
) -> Iterator[addict.Dict]:
    if payload is None:
        payload = {}

    if config is None:
        config = Config()

    collection = _get_collection_from_resource_path(resource_path, config.version)
    for r in filter_all(resource_path, payload, config):
        for item in r.json()['items']:
            yield response.transform(collection, item, version=config.version)

def filter_all_by_uuid_transformed(
    resource_path: str,
    payload: Mapping = None,
    uuids: List = None,
    uuids_per_request: int = 100,
    config: Config = None
) -> Iterator[addict.Dict]:
    if payload is None:
        payload = {}

    if uuids is None:
        uuids = []

    if config is None:
        config = Config()

    collection = _get_collection_from_resource_path(resource_path, config.version)
    for r in filter_all_by_uuid(
        resource_path,
        payload=payload,
        uuids=uuids,
        uuids_per_request=uuids_per_request,
        config=config
    ):
        for item in r.json()['items']:
            yield response.transform(collection, item, version=config.version)

def filter_all_by_id_transformed(
    resource_path: str,
    payload: Mapping = None,
    ids: List = None,
    ids_per_request: int = 100,
    config: Config = None
) -> Iterator[addict.Dict]:
    if payload is None:
        payload = {}

    if ids is None:
        ids = []

    if config is None:
        config = Config()

    collection = _get_collection_from_resource_path(resource_path, config.version)
    for r in filter_all_by_id(
        resource_path,
        payload=payload,
        ids=ids,
        ids_per_request=ids_per_request,
        config=config
    ):
        for item in r.json()['items']:
            yield response.transform(collection, item, version=config.version)


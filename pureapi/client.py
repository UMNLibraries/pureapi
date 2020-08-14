import copy
#import functools
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

env_key_varname = 'PURE_API_KEY'
def env_key() -> str:
    return os.environ.get(env_key_varname)

def default_protocol() -> str:
    return 'https'

def default_path() -> str:
    return 'ws/api'

def default_headers() -> MutableMapping:
    return {
        'Accept': 'application/json',
        'Accept-Charset': 'utf-8',
    }

def default_retryer() -> Callable:
    return Retrying(wait=wait_exponential(multiplier=1, max=60), reraise=True)

class PureAPIClientException(PureAPIException):
    pass

env_domain_varname = 'PURE_API_DOMAIN'
def env_domain() -> str:
    return os.environ.get(env_domain_varname)

def _get_collection_from_resource_path(resource_path: str, version: str) -> str:
    '''Extracts the collection name from a Pure API URL resource path.

    Args:
        resource_path: URL path, without the base URL, to a Pure API resource.
        config: Instance of pureapi.client.Config.

    Returns:
        The name of the collection.

    Raises:
        common.PureAPIInvalidCollectionError: If the extracted collection is invalid for the given API version.
    '''
    collection = resource_path.split('/')[0]
    if not valid_collection(collection=collection, version=version):
        raise PureAPIInvalidCollectionError(collection=collection, version=version)
    return collection

class PureAPIHTTPError(HTTPError, PureAPIClientException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PureAPIRequestException(RequestException, PureAPIClientException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

@attr.s(auto_attribs=True, frozen=True)
class Config():
    protocol: str = attr.ib(
        factory=default_protocol,
        validator=[
            attr.validators.instance_of(str),
            attr.validators.in_(['http','https']),
        ]
    )
    domain: str = attr.ib(
        factory=env_domain,
        validator=attr.validators.instance_of(str)
    )
    path: str = attr.ib(
        factory=default_path,
        validator=[
            attr.validators.instance_of(str),
        ]
    )
    version: str = attr.ib(
        factory=default_version,
        validator=attr.validators.instance_of(str)
    )
    @version.validator
    def validate_version(self, attribute, value):
        if not valid_version(value):
            raise PureAPIInvalidVersionError(value)
    key: str = attr.ib(
        factory=env_key,
        validator=attr.validators.instance_of(str)
    )
    headers: Mapping = attr.ib(
        factory=default_headers,
        validator=attr.validators.instance_of(MutableMapping)
    )
    retryer: Callable = attr.ib(
        factory=default_retryer,
        validator=attr.validators.is_callable()
    )
    base_url: str = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.headers['api-key'] = self.key
        object.__setattr__(self, 'base_url', f'{self.protocol}://{self.domain}/{self.path}/{self.version}/')

def get(resource_path: str, params: Mapping = None, config: Config = None) -> requests.Response:
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
    if params is None:
        params = {}

    if config is None:
        config = Config()

    r = get(resource_path, params={'size': 0, 'offset': 0}, config=config)
    json = r.json()
    record_count = int(json['count'])
    window_size = int(params['size']) if 'size' in params else 100
    window_count = int(math.ceil(float(record_count) / window_size))

    for window in range(0, window_count):
        offset = window * window_size
        size = window_size
        window_params = {'offset': offset, 'size': size}
        yield get(resource_path, params={**params, **window_params}, config=config)

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

def get_all_changes(token_or_date: str, params: Mapping = None, config: Config = None) -> Iterator[requests.Response]:
    if params is None:
        params = {}

    if config is None:
        config = Config()

    next_token_or_date = token_or_date
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
    token_or_date: str,
    params: Mapping = None,
    config: Config = None
) -> Iterator[addict.Dict]:
    if params is None:
        params = {}

    if config is None:
        config = Config()

    for r in get_all_changes(token_or_date, params, config):
        for item in r.json()['items']:
            yield response.transform('changes', item, version=config.version)

def filter(resource_path: str, payload: Mapping = None, config: Config = None) -> requests.Response:
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

    # TODO: Problems with these next few lines!
    count_payload = copy.deepcopy(payload)
    count_payload = payload
    count_payload['size'] = 0
    count_payload['offset'] = 0
    r = filter(resource_path, count_payload, config)
    json = r.json()
    record_count = int(json['count'])
    window_size = int(payload.setdefault('size', 100))
    if window_size <= 0:
        window_size = 100
    payload['size'] = window_size
    window_count = int(math.ceil(float(record_count) / window_size))

    for window in range(0, window_count):
        payload['offset'] = window * window_size
        yield filter(resource_path, payload, config)

def group_items(items: List = None, items_per_group: int = 100) -> Iterator[List]:
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

    for uuid_group in group_items(items=uuids, items_per_group=uuids_per_request):
        # TODO: Merge this with any payload passed in by the caller!
        payload = {
            'uuids': uuid_group,
            'size': len(uuid_group),
        }
        yield filter(resource_path, payload, config)

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

    for id_group in group_items(items=ids, items_per_group=ids_per_request):
        # TODO: Merge this with any payload passed in by the caller!
        payload = {
            'ids': id_group,
            'size': len(id_group),
        }
        yield filter(resource_path, payload, config)

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


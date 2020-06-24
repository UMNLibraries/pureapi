from collections.abc import Mapping # all dict-like classes
import copy
import functools
import os
import math

import requests
from requests.exceptions import RequestException, HTTPError
from tenacity import Retrying, wait_exponential

from pureapi import response
from pureapi.common import valid_collection, validate_version, PureAPIInvalidCollectionError
from pureapi.exceptions import PureAPIException

default_retryer = Retrying(wait=wait_exponential(multiplier=1, max=60), reraise=True)

env_key_varname = 'PURE_API_KEY'
def env_key():
    return os.environ.get(env_key_varname)
default_key = env_key()

default_headers = {
  'Accept': 'application/json',
  'Accept-Charset': 'utf-8',
  'api-key': default_key,
}

class PureAPIClientException(PureAPIException):
    pass

class PureAPIMissingKeyError(ValueError, PureAPIClientException):
    def __init__(self, *args, **kwargs):
        super().__init__(f'No API key found in kwargs, default_key, or {env_key_varname}', *args, **kwargs)

def validate_key(func):
    @functools.wraps(func)
    def wrapper_validate_key(*args, **kwargs):
        if 'headers' not in kwargs or kwargs['headers'] is None:
            kwargs['headers'] = default_headers if isinstance(default_headers, Mapping) else {}
        if 'api-key' not in kwargs['headers']:
            kwargs['headers']['api-key'] = None
        if kwargs['headers']['api-key'] is None:
            if 'key' in kwargs and kwargs['key'] is not None:
                kwargs['headers']['api-key'] = kwargs['key']
            elif default_key is not None:
                kwargs['headers']['api-key'] = default_key
            elif env_key() is not None:
                kwargs['headers']['api-key'] = env_key()
            else:
                raise PureAPIMissingKeyError()
        return func(*args, **kwargs)
    return wrapper_validate_key

env_domain_varname = 'PURE_API_DOMAIN'
def env_domain():
    return os.environ.get(env_domain_varname)
default_domain = env_domain()

class PureAPIMissingDomainError(ValueError, PureAPIClientException):
    def __init__(self, *args, **kwargs):
        super().__init__(f'No domain found in kwargs, default_domain, or {env_domain_varname}', *args, **kwargs)

def validate_domain(func):
    @functools.wraps(func)
    def wrapper_validate_domain(*args, **kwargs):
        if 'domain' not in kwargs:
            kwargs['domain'] = None
        if kwargs['domain'] is None:
            if default_domain is not None:
                kwargs['domain'] = default_domain
            elif env_domain() is not None:
                kwargs['domain'] = env_domain()
            else:
                raise PureAPIMissingDomainError()
        return func(*args, **kwargs)
    return wrapper_validate_domain

# Deprecate this:
default_url = env_url = os.environ.get('PURE_API_URL')

# Not going to allow env var settings for these, because I doubt anyone would ever use them.
default_protocol = 'https'
default_path = 'ws/api'

#@functools.lru_cache(maxsize=None)
@validate_version
@validate_domain
def construct_base_url(*, protocol=default_protocol, domain=None, path=default_path, version=None):
    return f'{protocol}://{domain}/{path}/{version}/'

def get_collection_from_resource_path(resource_path, *, version=None):
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

@validate_key
def get(
    resource_path,
    params={},
    *,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):

    base_url = construct_base_url(domain=domain, version=version)
    collection = get_collection_from_resource_path(resource_path, version=version)
    with requests.Session() as s:
        prepped = s.prepare_request(requests.Request('GET', base_url + resource_path, params=params))
        prepped.headers = {**prepped.headers, **headers}

        try:
            r = retryer(
                s.send,
                prepped
            )
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

def get_all(
    resource_path,
    params={},
    *,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    r = get(
        resource_path,
        params={'size': 0, 'offset': 0},
        domain=domain,
        version=version,
        key=key,
        headers=headers,
        retryer=retryer
    )

    json = r.json()
    record_count = int(json['count'])
    window_size = int(params['size']) if 'size' in params else 100
    window_count = int(math.ceil(float(record_count) / window_size))

    for window in range(0, window_count):
        offset = window * window_size
        size = window_size
        window_params = {'offset': offset, 'size': size}
        yield get(
            resource_path,
            params={**params, **window_params},
            domain=domain,
            version=version,
            key=key,
            headers=headers,
            retryer=retryer
        )

def get_all_transformed(
    resource_path,
    params={},
    *,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    collection = get_collection_from_resource_path(resource_path, version=version)
    for r in get_all(
        resource_path,
        params=params,
        domain=domain,
        version=version,
        key=key,
        headers=headers,
        retryer=retryer
    ):
        for item in r.json()['items']:
            yield response.transform(collection, item, version=version)

def get_all_changes(
    token_or_date,
    params={},
    *,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    next_token_or_date = token_or_date
    while(True):
        r = get(
            'changes/' + next_token_or_date,
            params=params,
            domain=domain,
            version=version,
            key=key,
            headers=headers,
            retryer=retryer
        )
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
    token_or_date,
    params={},
    *,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    for r in get_all_changes(
        token_or_date,
        params=params,
        domain=domain,
        version=version,
        key=key,
        headers=headers,
        retryer=retryer
    ):
        for item in r.json()['items']:
            yield response.transform('changes', item, version=version)

@validate_key
def filter(
    resource_path,
    payload={},
    *,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):

    base_url = construct_base_url(domain=domain, version=version)
    collection = get_collection_from_resource_path(resource_path, version=version)
    with requests.Session() as s:
        prepped = s.prepare_request(requests.Request('POST', base_url + resource_path, json=payload))
        prepped.headers = {**prepped.headers, **headers}

        try:
            r = retryer(
                s.send,
                prepped
            )
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

def filter_all(
    resource_path,
    payload={},
    *,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    count_payload = copy.deepcopy(payload)
    count_payload = payload
    count_payload['size'] = 0
    count_payload['offset'] = 0
    r = filter(
        resource_path,
        payload=count_payload,
        domain=domain,
        version=version,
        key=key,
        headers=headers,
        retryer=retryer
    )
    json = r.json()
    record_count = int(json['count'])
    window_size = int(payload.setdefault('size', 100))
    if window_size <= 0:
        window_size = 100
    payload['size'] = window_size
    window_count = int(math.ceil(float(record_count) / window_size))

    for window in range(0, window_count):
        payload['offset'] = window * window_size
        yield filter(
            resource_path,
            payload=payload,
            domain=domain,
            version=version,
            key=key,
            headers=headers,
            retryer=retryer
        )

default_items_per_group = 100
def group_items(items=[], items_per_group=default_items_per_group):
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
    resource_path,
    payload={},
    *,
    uuids=[],
    uuids_per_request=100,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    for uuid_group in group_items(items=uuids, items_per_group=uuids_per_request):
        payload = {
            'uuids': uuid_group,
            'size': len(uuid_group),
        }
        yield filter(
            resource_path,
            payload=payload,
            domain=domain,
            version=version,
            key=key,
            headers=headers,
            retryer=retryer
        )

def filter_all_by_id(
    resource_path,
    payload={},
    *,
    ids=[],
    ids_per_request=100,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    for id_group in group_items(items=ids, items_per_group=ids_per_request):
        payload = {
            'ids': id_group,
            'size': len(id_group),
        }
        yield filter(
            resource_path,
            payload=payload,
            domain=domain,
            version=version,
            key=key,
            headers=headers,
            retryer=retryer
        )

def filter_all_transformed(
    resource_path,
    payload={},
    *,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    collection = get_collection_from_resource_path(resource_path, version=version)
    for r in filter_all(
        resource_path,
        payload=payload,
        domain=domain,
        version=version,
        key=key,
        headers=headers,
        retryer=retryer
    ):
        for item in r.json()['items']:
            yield response.transform(collection, item, version=version)

def filter_all_by_uuid_transformed(
    resource_path,
    payload={},
    *,
    uuids=[],
    uuids_per_request=100,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    collection = get_collection_from_resource_path(resource_path, version=version)
    for r in filter_all_by_uuid(
        resource_path,
        payload=payload,
        uuids=uuids,
        uuids_per_request=uuids_per_request,
        domain=domain,
        version=version,
        key=key,
        headers=headers,
        retryer=retryer
    ):
        for item in r.json()['items']:
            yield response.transform(collection, item, version=version)

def filter_all_by_id_transformed(
    resource_path,
    payload={},
    *,
    ids=[],
    ids_per_request=100,
    domain=None,
    version=None,
    key=None,
    headers=None,
    retryer=default_retryer
):
    collection = get_collection_from_resource_path(resource_path, version=version)
    for r in filter_all_by_id(
        resource_path,
        payload=payload,
        ids=ids,
        ids_per_request=ids_per_request,
        domain=domain,
        version=version,
        key=key,
        headers=headers,
        retryer=retryer
    ):
        for item in r.json()['items']:
            yield response.transform(collection, item, version=version)


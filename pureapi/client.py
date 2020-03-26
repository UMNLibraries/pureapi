import copy
import os
import math
import requests
from tenacity import Retrying, wait_exponential
from . import response
from .exceptions import PureAPIClientException, PureAPIClientRequestException, PureAPIClientHTTPError
from requests.exceptions import RequestException, HTTPError

pure_api_version = os.environ.get('PURE_API_VERSION')
pure_api_url = os.environ.get('PURE_API_URL')
pure_api_key = os.environ.get('PURE_API_KEY')

headers = {
  'Accept': 'application/json',
  'Accept-Charset': 'utf-8',
  'api-key': pure_api_key,
}

retryer = Retrying(wait=wait_exponential(multiplier=1, max=60), reraise=True)

def get(endpoint, params={}, headers=headers, retryer=retryer):

  with requests.Session() as s:
    prepped = s.prepare_request(requests.Request('GET', pure_api_url + endpoint, params=params))
    prepped.headers = {**prepped.headers, **headers}

    try:
      r= retryer(
         s.send,
         prepped
      )
      r.raise_for_status()
      return r
    except HTTPError as http_exc:
      raise PureAPIClientHTTPError('GET request for endpoint {} with params {} returned HTTP status {}'.format(endpoint, params, http_exc.response.status_code), request=http_exc.request, response=http_exc.response) from http_exc
    except RequestException as req_exc:
      raise PureAPIClientRequestException('Failed GET request for endpoint {} with params {}'.format(endpoint, params), request=req_exc.request, response=req_exc.response) from req_exc
    except Exception as e:
      raise PureAPIClientException('Unexpected exception for GET request for endpoint {} with params {}'.format(endpoint, params)) from e

def get_all(endpoint, params={}, headers=headers, retryer=retryer):
  r = get(endpoint, params={'size': 0, 'offset': 0}, headers=headers, retryer=retryer)

  json = r.json()
  record_count = int(json['count'])
  window_size = int(params['size']) if 'size' in params else 100
  window_count = int(math.ceil(float(record_count) / window_size))

  for window in range(0, window_count):
    offset = window * window_size
    size = window_size
    window_params = {'offset': offset, 'size': size}
    yield get(endpoint, params={**params, **window_params}, headers=headers, retryer=retryer)

def get_all_transformed(endpoint, params={}, headers=headers, retryer=retryer):
  for r in get_all(endpoint, params=params, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)

def get_all_changes(token_or_date, params={}, headers=headers, retryer=retryer):
  next_token_or_date = token_or_date
  while(True):
    r = get('changes/' + next_token_or_date, params=params, headers=headers, retryer=retryer)
    yield r

    json = r.json()
    if json['moreChanges']:
      next_token_or_date = str(json['resumptionToken'])
    else:
      break

def get_all_changes_transformed(id_or_date, params={}, headers=headers, retryer=retryer):
  for r in get_all_changes(id_or_date, params=params, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform('changes', item)

def filter(endpoint, payload={}, headers=headers, retryer=retryer):
  with requests.Session() as s:
    prepped = s.prepare_request(requests.Request('POST', pure_api_url + endpoint, json=payload))
    prepped.headers = {**prepped.headers, **headers}

  try:
    r = retryer(
      s.send,
      prepped
    )
    r.raise_for_status()
    return r
  except HTTPError as http_exc:
    raise PureAPIClientHTTPError('GET request for endpoint {} with payload {} returned HTTP status {}'.format(endpoint, payload, http_exc.response.status_code), request=http_exc.request, response=http_exc.response) from http_exc
  except requests.exceptions.RequestException as req_exc:
    raise PureAPIClientRequestException('Failed POST request for endpoint {} with payload {}'.format(endpoint, payload), request=req_exc.request, response=req_exc.response) from req_exc
  except Exception as e:
    raise PureAPIClientException('Unexpected exception for POST request for endpoint {} with payload {}'.format(endpoint, payload)) from e

def filter_all(endpoint, payload={}, headers=headers, retryer=retryer):
  count_payload = copy.deepcopy(payload)
  count_payload = payload
  count_payload['size'] = 0
  count_payload['offset'] = 0
  r = filter(endpoint, payload=count_payload, headers=headers, retryer=retryer)
  json = r.json()
  record_count = int(json['count'])
  window_size = int(payload.setdefault('size', 100))
  if window_size <= 0:
    window_size = 100
  payload['size'] = window_size
  window_count = int(math.ceil(float(record_count) / window_size))

  for window in range(0, window_count):
    payload['offset'] = window * window_size
    yield filter(endpoint, payload=payload, headers=headers, retryer=retryer)

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

def filter_all_by_uuid(endpoint, uuids=[], uuids_per_request=100, payload={}, headers=headers, retryer=retryer):
  for uuid_group in group_items(items=uuids, items_per_group=uuids_per_request):
    payload = {
      'uuids': uuid_group,
      'size': len(uuid_group),
    }
    yield filter(endpoint, payload=payload, headers=headers, retryer=retryer)

def filter_all_by_id(endpoint, ids=[], ids_per_request=100, payload={}, headers=headers, retryer=retryer):
  for id_group in group_items(items=ids, items_per_group=ids_per_request):
    payload = {
      'ids': id_group,
      'size': len(id_group),
    }
    yield filter(endpoint, payload=payload, headers=headers, retryer=retryer)

def filter_all_transformed(endpoint, payload={}, headers=headers, retryer=retryer):
  for r in filter_all(endpoint, payload=payload, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)

def filter_all_by_uuid_transformed(endpoint, uuids=[], uuids_per_request=100, payload={}, headers=headers, retryer=retryer):
  for r in filter_all_by_uuid(endpoint, uuids=uuids, uuids_per_request=uuids_per_request, payload=payload, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)

def filter_all_by_id_transformed(endpoint, ids=[], ids_per_request=100, payload={}, headers=headers, retryer=retryer):
  for r in filter_all_by_id(endpoint, ids=ids, ids_per_request=ids_per_request, payload=payload, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)


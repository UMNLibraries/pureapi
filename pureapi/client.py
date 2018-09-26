import os
import math
import requests
from tenacity import Retrying, wait_exponential
from . import response
from .exceptions import PureAPIClientException, PureAPIClientRequestException

pure_api_url = os.environ.get('PURE_API_URL')
pure_api_key = os.environ.get('PURE_API_KEY')

headers = {
  'Accept': 'application/json',
  'Accept-Charset': 'utf-8',
  'api-key': pure_api_key,
}

retryer = Retrying(wait=wait_exponential(multiplier=1, max=60), reraise=True)

def get(endpoint, params={}, headers=headers, retryer=retryer):
  try:
    r= retryer(
      requests.get,
      pure_api_url + endpoint,
      params=params,
      headers=headers,
    )
    r.raise_for_status()
    return r
  except requests.exceptions.RequestException as req_exc:
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

def get_all_changes(id_or_date, params={}, headers=headers, retryer=retryer):
  next_id_or_date = id_or_date
  while(True):
    r = get('changes/' + next_id_or_date, params=params, headers=headers, retryer=retryer)
    yield r
    
    json = r.json()
    more_changes = json['moreChanges'] if 'moreChanges' in json else False
    if more_changes:
      next_id_or_date = str(json['lastId'])
    else:
      break

def get_all_changes_transformed(id_or_date, params={}, headers=headers, retryer=retryer):
  for r in get_all_changes(id_or_date, params=params, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform('changes', item)

def filter(endpoint, payload={}, headers=headers, retryer=retryer):
  try:
    r = retryer(
      requests.post,
      pure_api_url + endpoint,
      json=payload,
      headers=headers,
    )
    r.raise_for_status()
    return r
  except requests.exceptions.RequestException as req_exc:
    raise PureAPIClientRequestException('Failed POST request for endpoint {} with payload {}'.format(endpoint, payload), request=req_exc.request, response=req_exc.response) from req_exc
  except Exception as e:
    raise PureAPIClientException('Unexpected exception for POST request for endpoint {} with payload {}'.format(endpoint, payload)) from e

def filter_all(endpoint, payload={}, headers=headers, retryer=retryer):
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

def filter_all_by_uuid(endpoint, uuids=[], payload={}, headers=headers, retryer=retryer):
  payload['uuids'] = uuids
  return filter_all(endpoint, payload=payload, headers=headers, retryer=retryer)

def filter_all_by_id(endpoint, ids=[], payload={}, headers=headers, retryer=retryer):
  payload['ids'] = ids
  return filter_all(endpoint, payload=payload, headers=headers, retryer=retryer)

def filter_all_transformed(endpoint, payload={}, headers=headers, retryer=retryer):
  for r in filter_all(endpoint, payload=payload, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)

def filter_all_by_uuid_transformed(endpoint, uuids=[], payload={}, headers=headers, retryer=retryer):
  for r in filter_all_by_uuid(endpoint, uuids=uuids, payload=payload, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)

def filter_all_by_id_transformed(endpoint, ids=[], payload={}, headers=headers, retryer=retryer):
  for r in filter_all_by_id(endpoint, ids=ids, payload=payload, headers=headers, retryer=retryer):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)


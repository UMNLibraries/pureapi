import os
import math
import requests
from tenacity import retry, wait_exponential
from pureapi import response

pure_api_url = os.environ.get('PURE_API_URL')
pure_api_key = os.environ.get('PURE_API_KEY')

headers = {
  'Accept': 'application/json',
  'Accept-Charset': 'utf-8',
  'api-key': pure_api_key,
}

@retry(wait=wait_exponential(multiplier=1, max=60))
def get(endpoint, params={}, headers=headers):
  return requests.get(
    pure_api_url + endpoint,
    params=params,
    headers=headers,
  )
  
def get_all(endpoint, params={}, headers=headers):
  r = get(endpoint, {'size': 0, 'offset': 0}, headers)

  json = r.json()
  record_count = int(json['count'])
  window_size = int(params['size']) if 'size' in params else 100
  window_count = int(math.ceil(float(record_count) / window_size))

  for window in range(0, window_count):
    offset = window * window_size
    size = window_size
    window_params = {'offset': offset, 'size': size}
    try:
       yield get(endpoint, {**params, **window_params}, headers)
    except Exception as e:
      print('Failed request for endpoint {} with offset {} and size {}'.format(endpoint, offset, size))
      print(get.retry.statistics)
      raise e

def get_all_transformed(endpoint, params={}, headers=headers):
  for r in get_all(endpoint, params, headers):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)

def get_all_changes(id_or_date, params={}, headers=headers):
  next_id_or_date = id_or_date
  while(True):
    r = get('changes/' + next_id_or_date, params, headers)
    yield r
    
    json = r.json()
    more_changes = json['moreChanges'] if 'moreChanges' in json else False
    if more_changes:
      next_id_or_date = str(json['lastId'])
    else:
      break

def get_all_changes_transformed(id_or_date, params={}, headers=headers):
  for r in get_all_changes(id_or_date, params, headers):
    for item in r.json()['items']:
      yield response.transform('changes', item)

def filter(endpoint, payload={}, headers=headers):
  return requests.post(
    pure_api_url + endpoint,
    json=payload,
    headers=headers,
  )

def filter_all(endpoint, payload={}, headers=headers):
  count_payload = payload
  count_payload['size'] = 0
  count_payload['offset'] = 0
  r = filter(endpoint, count_payload, headers)
  json = r.json()
  record_count = int(json['count'])
  window_size = int(payload.setdefault('size', 100))
  if window_size >= 0:
    window_size = 100
  payload['size'] = window_size
  window_count = int(math.ceil(float(record_count) / window_size))

  for window in range(0, window_count):
     payload['offset'] = window * window_size
     yield filter(endpoint, payload, headers)

def filter_all_transformed(endpoint, payload={}, headers=headers):
  for r in filter_all(endpoint, payload, headers):
    for item in r.json()['items']:
      yield response.transform(endpoint, item)


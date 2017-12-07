import os
import math
import requests
from pureapi import response

pure_api_url = os.environ.get('PURE_API_URL')
pure_api_key = os.environ.get('PURE_API_KEY')

headers = {
  'Accept': 'application/json',
  'api-key': pure_api_key,
}

def get(endpoint, params={}, headers=headers):
  return requests.get(
    pure_api_url + endpoint,
    params=params,
    headers=headers
  )
  
def get_all(endpoint, params={}, headers=headers):
  r = get(endpoint, {'size': 0, 'offset': 0})
  json = r.json()
  record_count = int(json['count'])
  window_size = int(params['size']) if 'size' in params else 100
  window_count = int(math.ceil(float(record_count) / window_size))

  for window in range(0, window_count):
     window_params = {'offset': window * window_size, 'size': window_size}
     yield get(endpoint, {**params, **window_params})

def get_all_transformed(endpoint, params={}, headers=headers):
  for r in get_all(endpoint, params, headers):
    body_dict = r.json()
    for item in body_dict['items']:
      yield response.transform(endpoint, item)

import os
import requests
import math

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
  window_size = int(params['size']) if 'size' in params else 20
  window_count = int(math.ceil(float(record_count) / window_size))

  for window in range(0, window_count):
     window_params = {'offset': window * window_size}
     yield get(endpoint, {**params, **window_params})

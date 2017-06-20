from dotenv import load_dotenv, find_dotenv
import os
import requests
import math
import xml.etree.ElementTree as et

load_dotenv(find_dotenv())

pure_api_url = os.environ.get('PURE_API_URL')
pure_api_user = os.environ.get('PURE_API_USER')
pure_api_pass = os.environ.get('PURE_API_PASS')

def get(family, params={}):
  return requests.get(
    pure_api_url + family,
    auth=(pure_api_user, pure_api_pass),
    params=params
  )
  
def get_all(family, params={}):
  r = get(family, {"window.size": 1, "namespaces":"remove"})
  xml = et.fromstring(r.text)
  record_count = int(xml.find("count").text)
  window_size = int(params['window.size']) if 'window.size' in params else 20
  window_count = int(math.ceil(float(record_count) / window_size))

  for window in range(0, window_count):
     window_params = {'window.offset': window * window_size}
     yield get(family, {**params, **window_params})

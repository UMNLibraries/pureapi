from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from pureapi import client
import pprint
from addict import Dict

def test_get():
  r = client.get('organisational-units', {'size':1, 'offset':0})
  assert r.status_code == 200

  d = r.json()
  assert d['count'] > 0
  assert len(d['items']) == 1

  org = d['items'][0]
  uuid = org['uuid']

  r_uuid = client.get('organisational-units/' + uuid, {'size':1, 'offset':0})
  assert r_uuid.status_code == 200

  d_uuid = r.json()
  assert d_uuid['count'] > 0
  assert len(d_uuid['items']) == 1

  org_uuid = d_uuid['items'][0]
  assert org_uuid['uuid'] == uuid

def test_get_all_transformed():
  r = client.get('organisational-units', {'size':1, 'offset':0})
  d = r.json()
  count = d['count']

  transformed_count = 0
  for org in client.get_all_transformed('organisational-units'):
    assert isinstance(org, Dict)
    assert 'uuid' in org
    transformed_count += 1
  assert transformed_count == count

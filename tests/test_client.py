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

def test_get_all_addicts():
  r = client.get('organisational-units', {'size':1, 'offset':0})
  d = r.json()
  count = d['count']

  addicts_count = 0
  for org in client.get_all_addicts('organisational-units'):
    assert isinstance(org, Dict)
    assert 'uuid' in org
    addicts_count += 1
  assert addicts_count == count

#navlinks = parser.list(d, 'navigationLink')
##navlinks = parser.list(org, 'bogus')
#print(navlinks)
#for navlink in navlinks:
#  for key,val in navlink.items():
#    print("{} = {}".format(key, val))
#
#for org in d['items']:
#
#  name = org.name[0].value
#  #print(name)
#
#  start_date = org.period.startDate
#  #print(start_date)
#
#  # Test accessing a non-existent key:
#  bogus = parser.scalar(org, 'bogus')
#  #print(bogus)
#  
#

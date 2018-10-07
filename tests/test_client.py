from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from datetime import date, timedelta
from addict import Dict
import pytest
from pureapi import client
from pureapi.exceptions import PureAPIClientRequestException

def test_get():
  r_persons = client.get('persons', {'size':1, 'offset':0})
  assert r_persons.status_code == 200

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

def test_get_person_by_classified_source_id():
  emplid = '2110454'
  r = client.get('persons/' + emplid, {'idClassification':'classified_source'})
  assert r.status_code == 200

  person = r.json()
  for id in person['ids']:
    if id['typeUri'] == '/dk/atira/pure/person/personsources/employee':
      assert id['value'] == emplid

def test_get_all_changes():
  yesterday = date.today() - timedelta(days=1)
  for r in client.get_all_changes(yesterday.isoformat()):
    assert r.status_code == 200
    json = r.json()
    assert json['count'] > 0
    assert len(json['items']) > 0
    # There could be thousands of changes in a day, so we limit the test to one request:
    break

def test_get_all_changes_transformed():
  """
  Strange change records:
  {'family': 'dk.atira.pure.api.shared.model.event.Event', 'familySystemName': 'Event'}
  {'family': 'dk.atira.pure.api.shared.model.researchoutput.ResearchOutput', 'familySystemName': 'ResearchOutput'}
  """
  yesterday = date.today() - timedelta(days=1)
  transformed_count = 0
  transformed_limit = 10
  for change in client.get_all_changes_transformed(yesterday.isoformat()):
    assert isinstance(change, Dict)
    if 'configurationType' in change:
      assert 'identifier' in change
    elif change.familySystemName == 'Event':
      assert change.family == 'dk.atira.pure.api.shared.model.event.Event'
    elif change.familySystemName == 'ResearchOutput':
      assert change.family == 'dk.atira.pure.api.shared.model.researchoutput.ResearchOutput'
    else:
      for k in ['uuid', 'changeType', 'familySystemName', 'version']:
        assert k in change
    transformed_count += 1
    # There could be thousands of changes in a day, so we limit the records under test:
    if transformed_count == transformed_limit:
      break
  assert transformed_count == transformed_limit

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

  for person in client.get_all_transformed('persons'):
    assert isinstance(person, Dict)
    assert 'uuid' in person
    break

def test_filter():
  org_uuid = None
  for org in client.get_all_transformed('organisational-units', params={'size':1, 'offset':0}):
    org_uuid = org.uuid
    break

  payload = {
    "size": 1,
    "offset": 0,
    "forOrganisationalUnits": {
      "uuids": [
        org_uuid
      ]
    }
  }
  r = client.filter('research-outputs', payload)
  assert r.status_code == 200

  d = r.json()
  assert d['count'] > 0
  assert len(d['items']) == 1

@pytest.fixture(params=[x for x in range(0,3)])
def  test_group_items_params(request):
  params_sets = [
    {
     'items_per_group': 1,
     'expected_groups_count': 10,
     'items_in_last_group': 1,
    },
    {
     'items_per_group': 2,
     'expected_groups_count': 5,
     'items_in_last_group': 2,
    },
    {
     'items_per_group': 3,
     'expected_groups_count': 4,
     'items_in_last_group': 1,
    },
    {
     'items_per_group': 4,
     'expected_groups_count': 3,
     'items_in_last_group': 2,
    },
    {
     'items_per_group': 5,
     'expected_groups_count': 2,
     'items_in_last_group': 5,
    },
    {
     'items_per_group': 6,
     'expected_groups_count': 2,
     'items_in_last_group': 4,
    },
    {
     'items_per_group': 7,
     'expected_groups_count': 2,
     'items_in_last_group': 3,
    },
    {
     'items_per_group': 8,
     'expected_groups_count': 2,
     'items_in_last_group': 2,
    },
    {
     'items_per_group': 9,
     'expected_groups_count': 2,
     'items_in_last_group': 1,
    },
    {
     'items_per_group': 10,
     'expected_groups_count': 1,
     'items_in_last_group': 10,
    },
    # Kind of flukey that this works, but it does, due to there being only one expected group in this case:
    {
     'items_per_group': 11,
     'expected_groups_count': 1,
     'items_in_last_group': 10,
    },
  ]
  params_set = params_sets[request.param]
  yield params_set

def test_group_items(test_group_items_params):
  expected_groups_count = test_group_items_params['expected_groups_count']
  items_per_group = test_group_items_params['items_per_group']
  items_in_last_group = test_group_items_params['items_in_last_group']
  groups_count = 0
  for group in client.group_items([x for x in range(0,10)], items_per_group=items_per_group):
    groups_count += 1
    expected_items_in_group = items_in_last_group if groups_count == expected_groups_count else items_per_group
    assert len(group) == expected_items_in_group
  assert groups_count == expected_groups_count

def test_filter_all_by_uuid():
  expected_count = 13
  uuids = []
  for ro in client.get_all_transformed('research-outputs', params={'size': expected_count}):
    uuids.append(ro.uuid)
    if len(uuids) == expected_count:
      break
  downloaded_count = 0
  for r in client.filter_all_by_uuid('research-outputs', uuids=uuids, uuids_per_request=10):
    assert r.status_code == 200
    d = r.json()
    downloaded_count += d['count']
  downloaded_count == expected_count 

def test_filter_all_by_uuid_transformed():
  limit = 10
  uuids = []
  for ro in client.get_all_transformed('research-outputs', params={'size': limit}):
    uuids.append(ro.uuid)
    if len(uuids) == limit:
      break
  ros_by_uuid = []
  for ro in client.filter_all_by_uuid_transformed('research-outputs', uuids=uuids):
    assert ro.uuid in uuids
    ros_by_uuid.append(ro)
  assert len(ros_by_uuid) == len(uuids)

def test_filter_all_by_id():
  expected_count = 10
  ids = []
  for person in client.get_all_transformed('persons', params={'size': expected_count}):
    for _id in person.ids:
      if _id.type == 'Employee ID':
        ids.append(_id.value)
    if len(ids) == expected_count:
      break
  for r in client.filter_all_by_id('persons', ids=ids):
    assert r.status_code == 200
    d = r.json()
    # Should get only one response:
    assert d['count'] == expected_count 
    assert len(d['items']) == expected_count

def test_filter_all_by_id_transformed():
  limit = 10
  ids = []
  for person in client.get_all_transformed('persons', params={'size': limit}):
    for _id in person.ids:
      if _id.type == 'Employee ID':
        ids.append(_id.value)
    if len(ids) == limit:
      break
  persons_by_id = []
  for person in client.filter_all_by_id_transformed('persons', ids=ids):
    for _id in person.ids:
      if _id.type == 'Employee ID':
        assert _id.value in ids
    persons_by_id.append(person)
  assert len(persons_by_id) == len(ids)

def test_filter_all_transformed():
  type_uri = "/dk/atira/pure/organisation/organisationtypes/organisation/peoplesoft_deptid"
  payload = {
    "organisationalUnitTypeUri": [ 
      type_uri
    ]
  }
  r = client.filter('organisational-units', payload)
  d = r.json()
  count = d['count']

  transformed_count = 0
  for org in client.filter_all_transformed('organisational-units', payload):
    assert isinstance(org, Dict)
    assert 'uuid' in org
    assert org['type'][0]['uri'] == type_uri
    transformed_count += 1
  assert transformed_count == count

def test_get_exception():
  with pytest.raises(PureAPIClientRequestException):
    r = client.get('bogus', {'size':1, 'offset':0})

def test_filter_exception():
  with pytest.raises(PureAPIClientRequestException):
    r = client.filter('bogus', payload={})

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from datetime import date, timedelta
import importlib
import json
import os

from addict import Dict
import pytest
from requests.exceptions import HTTPError

from pureapi import client, common

from . import changes_including_zero_counts

@pytest.mark.forked
def test_config():
    # Remove any default config data from env vars:
    os.environ.pop(client.env_domain_varname)
    os.environ.pop(client.env_key_varname)
    os.environ.pop(common.env_version_varname)

    test_domain = 'example.com'
    test_key = '123'

    with pytest.raises(TypeError, match='domain'):
        client.Config()
    with pytest.raises(TypeError, match='key'):
        client.Config(domain=test_domain)
    with pytest.raises(common.PureAPIInvalidVersionError):
        client.Config(domain=test_domain, key=test_key, version='bogus')
    with pytest.raises(ValueError, match='protocol'):
        client.Config(domain=test_domain, key=test_key, protocol='bogus')
    with pytest.raises(TypeError, match='MutableMapping'):
        client.Config(domain=test_domain, key=test_key, headers='bogus')
    with pytest.raises(TypeError, match='callable'):
        client.Config(domain=test_domain, key=test_key, retryer='bogus')

    config = client.Config(domain=test_domain, key=test_key)
    assert config.headers['api-key'] == test_key
    assert (
        config.base_url
        ==
        f'{client.default_protocol()}://{test_domain}/{client.default_path()}/{common.default_version()}/'
    )

    if common.oldest_version != common.latest_version:
        # The default is the latest version. Test that we can override it with the Config param...
        config_oldest = client.Config(domain=test_domain, key=test_key, version=common.oldest_version)
        assert config_oldest.version == common.oldest_version
        assert (
            config_oldest.base_url
            ==
            f'{client.default_protocol()}://{test_domain}/{client.default_path()}/{common.oldest_version}/'
        )

        # ...and with an env var:
        os.environ[common.env_version_varname] = common.oldest_version
        config_oldest_env = client.Config(domain=test_domain, key=test_key)
        assert config_oldest_env.version == common.oldest_version
        assert (
            config_oldest_env.base_url
            ==
            f'{client.default_protocol()}://{test_domain}/{client.default_path()}/{common.oldest_version}/'
        )

def test_get_collection_from_resource_path():
    for resource_path in ('persons', 'persons/12345'):
        collection = client._get_collection_from_resource_path(
            resource_path,
            version=common.latest_version
        )
        assert collection == 'persons'

    with pytest.raises(common.PureAPIInvalidCollectionError):
        client._get_collection_from_resource_path('bogus', version=common.latest_version)

@pytest.mark.integration
def test_get(version):
    config = client.Config(version=version)
    r_persons = client.get('persons', {'size':1, 'offset':0}, config)
    assert r_persons.status_code == 200

    r = client.get('organisational-units', {'size':1, 'offset':0}, config)
    assert r.status_code == 200

    d = r.json()
    assert d['count'] > 0
    assert len(d['items']) == 1

    org = d['items'][0]
    uuid = org['uuid']

    r_uuid = client.get('organisational-units/' + uuid, {'size':1, 'offset':0}, config)
    assert r_uuid.status_code == 200

    d_uuid = r.json()
    assert d_uuid['count'] > 0
    assert len(d_uuid['items']) == 1

    org_uuid = d_uuid['items'][0]
    assert org_uuid['uuid'] == uuid

    # Tests for 5.16 schema changes:

    name_en = next(
        (name_text['value']
            for name_text
            in org_uuid['name']['text']
            if name_text['locale'] =='en_US'
        ),
        None
    )
    assert isinstance(name_en, str)
    assert len(name_en) > 0

    _type = next(
        (type_text['value']
            for type_text
            in org_uuid['type']['term']['text']
            if type_text['locale'] =='en_US'
        ),
        None
    ).lower()
    assert isinstance(_type, str)
    assert len(_type) > 0
    assert _type.islower()

    for _id in org_uuid['ids']:
        id_type_uri = _id['type']['uri']
        assert isinstance(id_type_uri, str)
        assert len(id_type_uri) > 0

        id_value = _id['value']['value']
        assert isinstance(id_value, str)
        assert len(id_value) > 0

@pytest.mark.integration
def test_get_person_by_classified_source_id(version):
    config = client.Config(version=version)
    emplid = '2110454'
    r = client.get('persons/' + emplid, {'idClassification':'classified_source'}, config)
    assert r.status_code == 200

    person = r.json()
    for _id in person['ids']:
        if _id['type']['uri'] == '/dk/atira/pure/person/personsources/employee':
            assert _id['value']['value'] == emplid

    # Tests for 5.16 schema changes:

    for staff_org_assoc in person['staffOrganisationAssociations']:
        job_descr = next(
            (job_descr_text['value']
                for job_descr_text
                in staff_org_assoc['jobDescription']['text']
                if job_descr_text['locale'] =='en_US'
            ),
            None
        )
        assert isinstance(job_descr, str)
        assert len(job_descr) > 0

        employment_type = next(
            (employment_type_text['value']
                for employment_type_text
                in staff_org_assoc['employmentType']['term']['text']
                if employment_type_text['locale'] =='en_US'
            ),
            None
        )
        assert isinstance(employment_type, str)
        assert len(employment_type) > 0

        staff_type = next(
            (staff_type_text['value']
                for staff_type_text
                in staff_org_assoc['staffType']['term']['text']
                if staff_type_text['locale'] =='en_US'
            ),
            None
        )
        assert isinstance(staff_type, str)
        assert len(staff_type) > 0

@pytest.mark.integration
def test_get_all_changes(version):
    config = client.Config(version=version)
    yesterday = date.today() - timedelta(days=1)
    request_count = 0
    for r in client.get_all_changes(yesterday.isoformat(), config=config):
        assert r.status_code == 200
        json = r.json()
        assert json['count'] > 0
        assert len(json['items']) > 0

        # There could be thousands of changes in a day, so we limit the number of requests:
        request_count += 1
        if request_count > 2:
            break

class MockResponse:
    def __init__(self, token_or_date):
        self.token_or_date = token_or_date

    def json(self):
        return json.loads(changes_including_zero_counts.changes[self.token_or_date])

def test_get_all_changes_skipping_zero_counts(monkeypatch):
    def mock_get(path, *args, **kwargs):
        (resource_path, token_or_date) = path.split('/')
        return MockResponse(token_or_date)

    monkeypatch.setattr(client, "get", mock_get)

    for r in client.get_all_changes('2020-03-12'):
        json = r.json()
        assert json['count'] > 0
        assert 'items' in json

@pytest.mark.integration
def test_get_all_changes_transformed(version):
    config = client.Config(version=version)
    """
    Strange change records:
    {'family': 'dk.atira.pure.api.shared.model.event.Event', 'familySystemName': 'Event'}
    {'family': 'dk.atira.pure.api.shared.model.researchoutput.ResearchOutput', 'familySystemName': 'ResearchOutput'}
    """
    yesterday = date.today() - timedelta(days=1)
    transformed_count = 0
    transformed_limit = 10
    for change in client.get_all_changes_transformed(yesterday.isoformat(), config=config):
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

@pytest.mark.integration
def test_get_all_transformed(version):
    config = client.Config(version=version)
    r = client.get('organisational-units', {'size':1, 'offset':0}, config)
    d = r.json()
    count = d['count']

    transformed_count = 0
    for org in client.get_all_transformed('organisational-units', config=config):
        assert isinstance(org, Dict)
        assert 'uuid' in org
        transformed_count += 1
    assert transformed_count == count

    for person in client.get_all_transformed('persons', config=config):
        assert isinstance(person, Dict)
        assert 'uuid' in person
        break

@pytest.mark.integration
def test_filter(version):
    config = client.Config(version=version)
    org_uuid = None
    for org in client.get_all_transformed('organisational-units', params={'size':1, 'offset':0}, config=config):
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
    r = client.filter('research-outputs', payload, config)
    assert r.status_code == 200

    d = r.json()
    assert d['count'] > 0
    assert len(d['items']) == 1

    # Tests for 5.16 schema changes:

    ro = d['items'][0]

    assert isinstance(ro['title']['value'], str)
    assert len(ro['title']['value']) > 0

    assert isinstance(ro['type']['uri'], str)
    assert len(ro['type']['uri']) > 0

    for pub_status in ro['publicationStatuses']:
        assert isinstance(pub_status['publicationStatus']['uri'], str)
        assert len(pub_status['publicationStatus']['uri']) > 0

    _type = next(
        (type_text['value']
            for type_text
            in ro['type']['term']['text']
            if type_text['locale'] =='en_US'
        ),
        None
    ).lower()
    assert isinstance(_type, str)
    assert len(_type) > 0
    assert _type.islower()

    for person_assoc in ro['personAssociations']:
        person_role = next(
            (person_role_text['value']
                for person_role_text
                in person_assoc['personRole']['term']['text']
                if person_role_text['locale'] =='en_US'
            ),
            None
        )
        assert isinstance(person_role, str)
        assert len(person_role) > 0


@pytest.fixture(params=[x for x in range(0,3)])
def test_group_items_params(request):
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

@pytest.mark.integration
def test_filter_all_by_uuid(version):
    config = client.Config(version=version)
    expected_count = 14
    ro_uuid_with_author_collaboration = '16e1efc1-92a2-4eca-a8d0-628bb2deda8a' # Not many records have these.
    uuids = [ro_uuid_with_author_collaboration]
    for ro in client.get_all_transformed('research-outputs', params={'size': expected_count}, config=config):
        uuids.append(ro.uuid)
        if len(uuids) == expected_count:
            break
    downloaded_count = 0
    for r in client.filter_all_by_uuid('research-outputs', uuids=uuids, uuids_per_request=10, config=config):
        assert r.status_code == 200
        d = r.json()
        downloaded_count += d['count']

        # Tests for 5.16 schema changes:
        for ro in d['items']:
            if ro['uuid'] != ro_uuid_with_author_collaboration:
                continue
            for person_assoc in ro['personAssociations']:
                if not 'authorCollaboration' in person_assoc:
                    continue
                author_collab = next(
                    (author_collab_text['value']
                        for author_collab_text
                        in person_assoc['authorCollaboration']['name']['text']
                        if author_collab_text['locale'] =='en_US'
                    ),
                    None
                )
                assert isinstance(author_collab, str)
                assert len(author_collab) > 0

    assert downloaded_count == expected_count

@pytest.mark.integration
def test_filter_all_by_uuid_transformed(version):
    config = client.Config(version=version)
    limit = 10
    uuids = []
    for ro in client.get_all_transformed('research-outputs', params={'size': limit}, config=config):
        uuids.append(ro.uuid)
        if len(uuids) == limit:
            break
    ros_by_uuid = []
    for ro in client.filter_all_by_uuid_transformed('research-outputs', uuids=uuids, config=config):
        assert ro.uuid in uuids
        ros_by_uuid.append(ro)
    assert len(ros_by_uuid) == len(uuids)

@pytest.mark.integration
def test_filter_all_by_id(version):
    config = client.Config(version=version)
    expected_count = 10
    ids = []
    for person in client.get_all_transformed('persons', params={'size': expected_count}, config=config):
        for _id in person.ids:
            if _id.type.uri == '/dk/atira/pure/person/personsources/employee':
                ids.append(_id.value.value)
        if len(ids) == expected_count:
            break
    for r in client.filter_all_by_id('persons', ids=ids, config=config):
        assert r.status_code == 200
        d = r.json()
        # Should get only one response:
        assert d['count'] == expected_count
        assert len(d['items']) == expected_count

@pytest.mark.integration
def test_filter_all_by_id_transformed(version):
    config = client.Config(version=version)
    limit = 10
    ids = []
    for person in client.get_all_transformed('persons', params={'size': limit}, config=config):
        for _id in person.ids:
            if _id.type.uri == '/dk/atira/pure/person/personsources/employee':
                ids.append(_id.value.value)
        if len(ids) == limit:
            break
    persons_by_id = []
    for person in client.filter_all_by_id_transformed('persons', ids=ids, config=config):
        for _id in person.ids:
            if _id.type.uri == '/dk/atira/pure/person/personsources/employee':
                assert _id.value.value in ids
        persons_by_id.append(person)
    assert len(persons_by_id) == len(ids)

@pytest.mark.integration
def test_filter_all_transformed(version):
    config = client.Config(version=version)
    type_uri = "/dk/atira/pure/organisation/organisationtypes/organisation/peoplesoft_deptid"
    payload = {
        "organisationalUnitTypeUris": [
            type_uri
        ]
    }
    r = client.filter('organisational-units', payload, config)
    d = r.json()
    count = d['count']

    transformed_count = 0
    for org in client.filter_all_transformed('organisational-units', payload, config=config):
        assert isinstance(org, Dict)
        assert 'uuid' in org
        assert org['type'][0]['uri'] == type_uri
        transformed_count += 1
    assert transformed_count == count

@pytest.mark.integration
def test_get_exception(version):
    config = client.Config(version=version)
    with pytest.raises(client.PureAPIHTTPError, match='404') as exc_info:
        client.get('persons/bogus-id', config=config)
    assert exc_info.errisinstance(HTTPError)

@pytest.mark.integration
def test_filter_exception(version):
    config = client.Config(version=version)
    #with pytest.raises(client.PureAPIHTTPError, match='404') as exc_info:
    with pytest.raises(client.PureAPIHTTPError, match='500') as exc_info:
        payload = {
            "size": 1,
            "offset": 0,
            "forOrganisationalUnits": {
                "uuids": [
                    'bogus-id' # Have no idea why this triggers a 500 status, but just going with it.
                ]
            }
        }
        r = client.filter('persons', payload=payload, config=config)
    assert exc_info.errisinstance(HTTPError)

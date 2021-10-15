from datetime import datetime
import json
import re

from addict import Dict
import pytest

from pureapi import response
from pureapi.common import PureAPIInvalidCollectionError, PureAPIInvalidVersionError

uuid_regex = re.compile('^[a-z0-9-]+$')

def iso_8601_string_to_datetime(iso_8601_string):
    return datetime.strptime(
        iso_8601_string,
        '%Y-%m-%dT%H:%M:%S.%f%z',
    )

def test_transformer_for(version):
    expected_transformer = getattr(response, 'research_output_' + version)
    transformer = response.transformer_for(
        collection='research-outputs',
        version=version
    )
    assert transformer is expected_transformer

    # We have no transformer function for activities,
    # so we should get the default transformer:
    assert response.transformer_for(
        collection='activities',
        version=version
    ) == response.default

    with pytest.raises(PureAPIInvalidCollectionError):
        response.transformer_for(
            collection='bogus',
            version=version
        )

    with pytest.raises(PureAPIInvalidVersionError):
        response.transformer_for(
            collection='persons',
            version='bogus'
        )

def test_transform(version):
    citation_count = None
    ro = response.transform(
        'research-outputs',
        {},
        version=version
    )
    assert isinstance(ro, Dict)
    assert ro.totalScopusCitations == citation_count

    with pytest.raises(PureAPIInvalidCollectionError):
        response.transform(
            'bogus',
            {},
            version=version
        )

    with pytest.raises(PureAPIInvalidVersionError):
        response.transform(
            'persons',
            {},
            version='bogus'
        )

def test_person(version):
    transformer = getattr(response, 'person_' + version)

    # Test defaults for fields that may be missing:
    p = transformer({})
    assert isinstance(p, Dict)
    assert p.info.previousUuids == []
    assert p.name.firstName == None
    assert p.name.lastName == None
    assert p.externalId == None
    assert p.scopusHIndex == None
    assert p.orcid == None

    p2 = transformer({'name': {'lastName': 'Valiullin'}})
    assert p2.name.firstName == None
    assert p2.name.lastName == 'Valiullin'

    # Test that we can correctly find existing, populated fields:
    jan_fransen_uuid = '01edf3d8-7e44-4dfa-bec4-8e3472965e1f'
    with open(f'tests/fixtures/{version}/person/{jan_fransen_uuid}.json') as f:
        p3 = transformer(json.load(f))
        assert isinstance(p3.uuid, str)
        assert p3.uuid == jan_fransen_uuid
        id_type_uri_value_map = {
            '/dk/atira/pure/person/personsources/scopusauthor': '36713379400',
            '/dk/atira/pure/person/personsources/employee': '1164667',
            '/dk/atira/pure/person/personsources/umn': 'fransen',
        }
        for _id in p3.ids:
            if _id.type.uri in id_type_uri_value_map:
                assert isinstance(_id.value.value, str)
                assert _id.value.value == id_type_uri_value_map[_id.type.uri]
        assert isinstance(p3.externalId, str)
        assert p3.externalId == '3568'
        assert isinstance(p3.name.firstName, str)
        assert p3.name.firstName == 'Jan'
        assert isinstance(p3.name.lastName, str)
        assert p3.name.lastName == 'Fransen'
        assert isinstance(p3.orcid, str)
        assert p3.orcid == '0000-0002-0302-2761'
        assert isinstance(p3.scopusHIndex, int)
        assert isinstance(iso_8601_string_to_datetime(p3.info.modifiedDate), datetime)

        for org_assoc in p3.staffOrganisationAssociations:
            assert uuid_regex.match(org_assoc.organisationalUnit.uuid) is not None
            assert isinstance(iso_8601_string_to_datetime(org_assoc.period.startDate), datetime)
            assert isinstance(org_assoc.isPrimaryAssociation, bool)

            job_description = next(
                (job_description_text.value
                     for job_description_text
                     in org_assoc.jobDescription.text
                     if job_description_text.locale =='en_US'
                ),
                None
            )
            assert isinstance(job_description, str)

            employed_as = next(
                (employment_type_text.value
                    for employment_type_text
                    in org_assoc.employmentType.term.text
                    if employment_type_text.locale =='en_US'
                ),
                None
            )
            # employed_as will be None for some jobs:
            if org_assoc.affiliationId in ['9713','9714']:
                assert isinstance(employed_as, str)

            staff_type = re.sub('[^a-zA-Z]+', '', next(
                (staff_type_text.value
                    for staff_type_text
                    in org_assoc.staffType.term.text
                    if staff_type_text.locale =='en_US'
                ),
                None
            ).lower())
            assert isinstance(staff_type, str)

def test_external_person(version):
    transformer = getattr(response, 'external_person_' + version)
    p = transformer({})
    assert isinstance(p, Dict)
    assert p.info.previousUuids == []
    assert p.name.firstName == None
    assert p.name.lastName == None

    p2 = transformer({'name': {'firstName': 'Darth', 'lastName': 'Vader'}})
    assert p2.name.firstName == 'Darth'
    assert p2.name.lastName == 'Vader'

def test_organisational_unit(version):
    transformer = getattr(response, 'organisational_unit_' + version)
    ou = transformer({})
    assert isinstance(ou, Dict)
    assert ou.info.previousUuids == []
    assert ou.externalId == None
    assert ou.ids == []
    assert ou.parents[0].uuid == None

    # Test that we can correctly find existing, populated fields:
    libraries_uuid = '3f714cea-399a-4fec-971f-45e047806367'
    with open(f'tests/fixtures/{version}/organisational_unit/{libraries_uuid}.json') as f:
        ou2 = transformer(json.load(f))
        assert isinstance(ou2.uuid, str)
        assert ou2.uuid == libraries_uuid
        assert isinstance(ou2.externalId, str)
        assert ou2.externalId == 'LKTQDNVXHPZC'
        assert isinstance(iso_8601_string_to_datetime(ou2.info.modifiedDate), datetime)
        assert isinstance(ou2.parents[0].uuid, str)
        assert ou2.parents[0].uuid == '0db47450-6e7d-464b-a1cb-9c8b571ca060' # UMN Twin Cities

        ou2_name = next(
            (name_text.value
                for name_text
                in ou2.name.text
                if name_text.locale =='en_US'
            ),
            None
        )
        assert isinstance(ou2_name, str)
        assert ou2_name == 'University Libraries'

        ou2_type = next(
            (type_text.value
                for type_text
                in ou2.type.term.text
                if type_text.locale =='en_US'
            ),
            None
        ).lower()
        assert isinstance(ou2_type, str)
        assert ou2_type == 'college'

    # externalId is not always defined, in which case we look for our UMN-defined organisation IDs,
    # which we call the "pure ID", in the "ids" list instead:
    clawriting_uuid = 'cb612e38-13be-4496-aafa-02ea96ddeca4'
    clawriting_pure_id = 'CLAWRITING'
    with open(f'tests/fixtures/{version}/organisational_unit/{clawriting_uuid}.json') as f:
        ou3 = transformer(json.load(f))
        assert isinstance(ou3.uuid, str)
        assert ou3.uuid == clawriting_uuid
        assert isinstance(ou3.externalId, str)
        assert ou3.externalId == clawriting_pure_id
        ou3_pure_id = next(
            (
                _id.value.value
                for _id in ou3.ids
                if _id.type.uri =='/dk/atira/pure/organisation/organisationsources/organisationid'
            ),
            None
        )
        assert isinstance(ou3_pure_id, str)
        assert ou3_pure_id == clawriting_pure_id

def test_external_organisation(version):
    transformer = getattr(response, 'external_organisation_' + version)
    eo = transformer({})
    assert isinstance(eo, Dict)
    assert eo.info.previousUuids == []
    assert eo.pureId == None

def test_research_output(version):
    transformer = getattr(response, 'research_output_' + version)
    ro1_citation_count = 100
    ro1 = transformer({'totalScopusCitations': ro1_citation_count})
    assert isinstance(ro1, Dict)
    assert ro1.electronicVersions == []
    assert ro1.info.additionalExternalIds == []
    assert ro1.info.previousUuids == []
    assert ro1.totalScopusCitations == ro1_citation_count
    assert ro1.volume == None
    assert ro1.journalNumber == None
    assert ro1.pages == None

    ro2_citation_count = None
    ro2 = transformer({})
    assert isinstance(ro2, Dict)
    assert ro2.info.previousUuids == []
    assert ro2.totalScopusCitations == ro2_citation_count

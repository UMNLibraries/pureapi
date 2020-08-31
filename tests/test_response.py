from pureapi import response
from pureapi.common import PureAPIInvalidCollectionError, PureAPIInvalidVersionError
from addict import Dict
import pytest

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

from datetime import datetime
import itertools
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

    # Test that we can correctly find existing, populated fields:
    sambrano_uuid = 'f6aa0ce4-66b4-4e42-b355-709a7d7bfa48'
    with open(f'tests/fixtures/{version}/external_person/{sambrano_uuid}.json') as f:
        p3 = transformer(json.load(f))
        assert isinstance(p3.uuid, str)
        assert p3.uuid == sambrano_uuid
        id_type_uri_value_map = {
            '/dk/atira/pure/externalperson/externalpersonsources/scopusauthor': '6603637835',
        }
        for _id in p3.ids:
            if _id.type.uri in id_type_uri_value_map:
                assert isinstance(_id.value.value, str)
                assert _id.value.value == id_type_uri_value_map[_id.type.uri]
        assert isinstance(p3.name.firstName, str)
        assert p3.name.firstName == 'Gilberto R.'
        assert isinstance(p3.name.lastName, str)
        assert p3.name.lastName == 'Sambrano'
        assert isinstance(iso_8601_string_to_datetime(p3.info.modifiedDate), datetime)

        for org_assoc in p3.externalOrganisations:
            assert isinstance(org_assoc.uuid, str)
            assert uuid_regex.match(org_assoc.uuid) is not None

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

    # Test that we can correctly find existing, populated fields:
    rutherford_lab_uuid = '53c9eb4e-01cf-48b2-86cd-58581aa8a7ab'
    with open(f'tests/fixtures/{version}/external_organisation/{rutherford_lab_uuid}.json') as f:
        eo2 = transformer(json.load(f))
        assert isinstance(eo2.uuid, str)
        assert eo2.uuid == rutherford_lab_uuid
        assert isinstance(iso_8601_string_to_datetime(eo2.info.modifiedDate), datetime)

        eo2_name = next(
            (name_text.value
                for name_text
                in eo2.name.text
                if name_text.locale =='en_US'
            ),
            None
        )
        assert isinstance(eo2_name, str)
        assert eo2_name == 'Rutherford Appleton Laboratory'

        eo2_type = next(
            (type_text.value
                for type_text
                in eo2.type.term.text
                if type_text.locale =='en_US'
            ),
            None
        ).lower()
        assert isinstance(eo2_type, str)
        assert eo2_type == 'government'

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

    # Test that we can correctly find existing, populated fields:
    cabbibo_decays_uuid = 'f145e583-7d49-415e-aefb-381905b58ae7'
    with open(f'tests/fixtures/{version}/research_output/{cabbibo_decays_uuid}.json') as f:
        ro3 = transformer(json.load(f))
        assert isinstance(ro3.uuid, str)
        assert ro3.uuid == cabbibo_decays_uuid

        assert isinstance(iso_8601_string_to_datetime(ro3.info.modifiedDate), datetime)

        assert isinstance(ro3.externalId, str)
        assert ro3.externalId == '85002158060'

        assert isinstance(ro3.externalIdSource, str)
        assert ro3.externalIdSource == 'Scopus'

        ro3_doi = None
        for version in ro3.electronicVersions:
            if 'doi' in version:
                ro3_doi = version.doi
        assert isinstance(ro3_doi, str)
        assert ro3_doi == 'https://doi.org/10.1103/PhysRevLett.117.232002'

        ro3_pmid = None
        ro3_qabo_id = None
        for _id in ro3.info.additionalExternalIds:
            if _id.idSource == 'PubMed':
                ro3_pmid = _id.value
            if _id.idSource == 'QABO':
                ro3_qabo_id = _id.value
        assert isinstance(ro3_pmid, str)
        assert ro3_pmid == '27982610'
        assert isinstance(ro3_qabo_id, str)
        assert ro3_qabo_id == '85002158060'

        type_uri_parts = ro3.type.uri.split('/')
        type_uri_parts.reverse()
        pure_subtype, pure_type, pure_parent_type = type_uri_parts[0:3]
        assert isinstance(pure_type, str)
        assert pure_type == 'contributiontojournal'
        assert isinstance(pure_subtype, str)
        assert pure_subtype == 'article'

        assert isinstance(ro3.title.value, str)
        assert ro3.title.value == 'Measurement of Singly Cabibbo Suppressed Decays Λc+ →pπ+π- and Λc+ →pK+K-'

        assert isinstance(ro3.journalAssociation.title.value, str)
        assert ro3.journalAssociation.title.value == 'Physical review letters'

        assert isinstance(ro3.journalAssociation.issn.value, str)
        assert ro3.journalAssociation.issn.value == '0031-9007'

        pub_state = ro3.publicationStatuses[0]
        state_uri_parts = pub_state.publicationStatus.uri.split('/')
        state_uri_parts.reverse()
        assert isinstance(state_uri_parts[0], str)
        assert state_uri_parts[0] == 'published'
        assert isinstance(pub_state.current, bool)
        assert pub_state.current is True
        assert isinstance(pub_state.publicationDate.year, int)
        assert pub_state.publicationDate.year == 2016
        assert isinstance(pub_state.publicationDate.month, int)
        assert pub_state.publicationDate.month == 12
        assert isinstance(pub_state.publicationDate.day, int)
        assert pub_state.publicationDate.day == 2

        assert isinstance(ro3.volume, str)
        assert ro3.volume == '117'
        assert isinstance(ro3.journalNumber, str)
        assert ro3.journalNumber == '23'
        assert isinstance(ro3.totalScopusCitations, int)
        assert ro3.totalScopusCitations == 21

        # Forgot to query for 'pages' when searching for an example record with
        # values for all the fields we use. Doesn't seem worth it to start over
        # with a different record just for this field. To see that 'pages' is
        # where we expect in the schema, with values we expect, at least
        # through API version 5.21, refer to record with uuid:
        # dd5ff80a-0725-43e4-aaa3-47f4ebb2b998.
        assert ro3.pages is None

        assert isinstance(ro3.managingOrganisationalUnit.uuid, str)
        assert ro3.managingOrganisationalUnit.uuid == '02b1196e-a592-4f52-8667-b94610d81b8e'

        found_author_collab = False
        for author_assoc in ro3.personAssociations:
            if 'authorCollaboration' in author_assoc:
                found_author_collab = True
                assert isinstance(author_assoc.authorCollaboration.uuid, str)
                assert author_assoc.authorCollaboration.uuid == '965013d0-149d-4178-b54a-a43d3be26f12'
                author_collab_name = next(
                    (author_collab_text.value
                        for author_collab_text
                        in author_assoc.authorCollaboration.name.text
                        if author_collab_text.locale =='en_US'
                    ),
                    None
                )
                assert isinstance(author_collab_name, str)
                assert author_collab_name == '(BESIII Collaboration)'
            if 'person' in author_assoc:
                assert isinstance(author_assoc.person.uuid, str)
            if 'externalPerson' in author_assoc:
                assert isinstance(author_assoc.externalPerson.uuid, str)
            if 'person' in author_assoc or 'externalPerson' in author_assoc:
                assert isinstance(author_assoc.name.firstName, str)
                assert isinstance(author_assoc.name.lastName, str)
                for pure_org in itertools.chain(author_assoc.organisationalUnits, author_assoc.externalOrganisations):
                    assert isinstance(pure_org.uuid, str)


            author_role = next(
                (author_role_text.value
                    for author_role_text
                    in author_assoc.personRole.term.text
                    if author_role_text.locale =='en_US'
                ),
                None
            ).lower()
            assert isinstance(author_role, str)

        assert found_author_collab is True






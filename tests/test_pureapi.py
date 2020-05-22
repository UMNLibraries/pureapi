import pytest
import importlib
import pureapi
from pureapi.exceptions import PureAPIInvalidVersionError, PureAPIInvalidCollectionError, PureAPIMissingDomainError

def test_valid_version():
    versions = pureapi.versions
    assert len(versions) > 0
    assert all(pureapi.valid_version(version) for version in versions)
    assert not pureapi.valid_version('bogus')

def test_latest_version():
    # Doesn't test that latest_version actually is the latest version,
    # because that would just duplicate the code under test.
    assert pureapi.latest_version in pureapi.versions
    assert pureapi.valid_version(pureapi.latest_version)

def test_default_version():
    # We reload pureapi here because the behavior under test is affected by env vars,
    # which may have been set by previously run tests.
    importlib.reload(pureapi)
    assert pureapi.default_version in pureapi.versions
    assert pureapi.valid_version(pureapi.default_version)

def test_construct_base_url():
    # We reload pureapi here because the behavior under test is affected by env vars,
    # which may have been set by previously run tests.
    importlib.reload(pureapi)
    domain='experts.umn.edu'

    assert (
        pureapi.construct_base_url(domain=domain, version=pureapi.default_version)
        ==
        f'{pureapi.default_protocol}://{domain}/{pureapi.default_path}/{pureapi.default_version}/'
    )

    with pytest.raises(PureAPIInvalidVersionError):
        pureapi.construct_base_url(domain='experts.umn.edu', version='bogus')

    with pytest.raises(PureAPIMissingDomainError):
        pureapi.construct_base_url()

def test_schemas_for_all_versions():
    # For here and now, at least, we just assert that the schema for each version is an
    # object with some number of things in it. Should work for just about any object we
    # would use to represent a schema.
    assert all(len(pureapi.schema(version=version)) for version in pureapi.versions)
    with pytest.raises(PureAPIInvalidVersionError):
         schema = pureapi.schema(version='bogus')

def test_collections_for_all_versions():
    for version in pureapi.versions:
        collections = pureapi.collections(version=version)
        assert len(collections) > 0
        for collection in collections:
            assert pureapi.valid_collection(collection=collection, version=version)
        assert not pureapi.valid_collection(collection='bogus', version=version)
        with pytest.raises(PureAPIInvalidVersionError):
            collections = pureapi.collections(version='bogus')

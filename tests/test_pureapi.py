import pureapi
from pureapi.exceptions import PureAPIInvalidVersionError, PureAPIInvalidCollectionError
import pytest

def test_valid_version():
    versions = pureapi.versions
    assert len(versions) > 0
    for version in versions:
        assert pureapi.valid_version(version)
    assert not pureapi.valid_version('bogus')

def test_schemas_for_all_versions():
    for version in pureapi.versions:
        # For here and now, at least, we just assert that the schema for each version is an
        # object with some number of things in it. Should work for just about any object we
        # would use to represent a schema.
        assert len(pureapi.schema(version=version)) > 0
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

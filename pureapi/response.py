import os
from typing import Callable, MutableMapping

from addict import Dict

from pureapi.common import validate_collection

def default(record: MutableMapping) -> Dict:
    '''Default record transformer. Just transforms a mapping (most likely a
    ``dict``) to an ``addict.Dict`` object.

    Args:
        record: A mapping represenation of a Pure API JSON record.

    Returns:
        A transformed record.
    '''
    d = Dict(record)
    return d

def change(record: MutableMapping) -> Dict:
    '''Transforms a record from the ``changes`` collection.

    Args:
        record: A mapping represenation of a Pure API JSON record.

    Returns:
        A transformed record.
    '''
    d = Dict(record)
    return d
change_524 = change
'''``change_524()`` is an alias of ``change()``.'''

def external_organisation(record: MutableMapping) -> Dict:
    '''Transforms a record from the ``external-organisations`` collection.

    Ensures that the ``pureId`` (default ``None``) and ``info.previousUuids``
    (default ``[]``) fields exist.

    Args:
        record: A mapping represenation of a Pure API JSON record.

    Returns:
        A transformed record.
    '''
    d = Dict(record)
    d.info.setdefault('previousUuids', [])
    d.setdefault('pureId', None)
    return d
external_organisation_524 = external_organisation
'''``external_organisation_524`` is an alias of ``external_organisation()``.'''

def external_person(record: MutableMapping) -> Dict:
    '''Transforms a record from the ``external-persons`` collection.

    Ensures that the ``info.previousUuids`` (default ``[]``), ``name.firstName``
    (default ``None``), and ``name.lastName`` (default ``None``) fields exist.

    Args:
        record: A mapping represenation of a Pure API JSON record.

    Returns:
        A transformed record.
    '''
    d = Dict(record)
    d.info.setdefault('previousUuids', [])
    d.setdefault('name', Dict())
    d.name.setdefault('firstName', None)
    d.name.setdefault('lastName', None)
    return d
external_person_524 = external_person
'''``external_person_524`` is an alias of ``external_person()``.'''

def organisational_unit(record: MutableMapping) -> Dict:
    '''Transforms a record from the ``organisational-units`` collection.

    Ensures that the ``externalId`` (default ``None``), ``ids`` (default ``[]``),
    ``info.previousUuids`` (default ``[]``), and ``parents`` (default
    ``[{Dict({'uuid'}: None})]``) fields exist.

    Args:
        record: A mapping represenation of a Pure API JSON record.

    Returns:
        A transformed record.
    '''
    d = Dict(record)
    d.info.setdefault('previousUuids', [])

    # We've been calling the externalId the pure_id, but really it's our old
    # internal (SciVal?) identifier. Pure defines a separate pureId, which we
    # may want to store later.
    d.setdefault('externalId', None)

    # Also, now that we are doing all organisation data entry in Pure, we sometimes
    # add our pure_id the same way we do PeopleSoft DeptIDs. In this case, it will
    # be in the list of ids in the json record. Make sure this list always exists:
    d.setdefault('ids', [])

    # Some orgs may not have parents, e.g., University of Minnesota.
    d.setdefault('parents', [Dict({'uuid': None})])

    return d
organisational_unit_524 = organisational_unit
'''``organisational_unit_524`` is an alias of ``organisational_unit()``.'''

def person(record: MutableMapping) -> Dict:
    '''Transforms a record from the ``persons`` collection.

    Ensures that the ``info.previousUuids`` (default ``[]``), ``name.firstName``
    (default ``None``), ``name.lastName`` (default ``None``), ``externalId``
    (default ``None``), ``scopusHIndex`` (default ``None``), and ``orcid``
    (default ``None``) fields exist.

    Args:
        record: A mapping represenation of a Pure API JSON record.

    Returns:
        A transformed record.
    '''
    d = Dict(record)
    d.info.setdefault('previousUuids', [])
    d.setdefault('name', Dict())
    d.name.setdefault('firstName', None)
    d.name.setdefault('lastName', None)

    # We've been calling the externalId the pure_id, but really it's our old
    # internal (SciVal?) identifier. Pure defines a separate pureId, which we
    # may want to store later.
    d.setdefault('externalId', None)
    d.setdefault('scopusHIndex', None)
    d.setdefault('orcid', None)
    return d
person_524 = person
'''``person_524`` is an alias of ``person()``.'''

def research_output(record: MutableMapping) -> Dict:
    '''Transforms a record from the ``research-outputs`` collection.

    Ensures that the ``info.additionalExternalIds`` (default ``[]``),
    ``info.previousUuids`` (default ``[]``), ``electronicVersions``
    (default ``[]``), ``volume`` (default ``None``), ``journalNumber``
    (default ``None``), ``pages`` (default ``None``), and
    ``totalScopusCitations`` (default ``None``) fields exist.

    Args:
        record: A mapping represenation of a Pure API JSON record.

    Returns:
        A transformed record.
    '''
    d = Dict(record)
    d.setdefault('electronicVersions', [])
    d.info.setdefault('additionalExternalIds', [])
    d.info.setdefault('previousUuids', [])
    d.setdefault('volume', None)
    d.setdefault('journalNumber', None)
    d.setdefault('pages', None)
    d.setdefault('totalScopusCitations', None)
    return d
research_output_524 = research_output
'''``research_output_524`` is an alias of ``research_output()``.'''

@validate_collection
def transformer_for(*, collection: str, version: str = None) -> Callable[[MutableMapping], Dict]:
    '''Returns a record transformer function for a given collection name and
    version.

    Args:
        collection: The name of the collection to which the record belongs.
        version: The Pure API version, without the decimal point.

    Returns:
        A transformer function.

    Raises:
        common.PureAPIInvalidCollectionError: If the collection name is
            invalid for the given API version.
        common.PureAPIInvalidVersionError: If the API version number
            is unrecognized.
    '''
    transformer_basename = {
        'changes': 'change',
        'external-organisations': 'external_organisation',
        'external-persons': 'external_person',
        'organisational-units': 'organisational_unit',
        'persons': 'person',
        'research-outputs': 'research_output',
    }.get(collection, None)
    transformer_name = 'default' if transformer_basename is None else f'{transformer_basename}_{version}'
    return globals()[transformer_name]

def transform(collection: str, record: MutableMapping, *, version: str = None) -> Dict:
    '''Transforms a ``record`` mapping (most likely a ``dict``) from a given
    ``collection`` and ``version`` to an ``addict.Dict`` object.

    The returned objects allow for easier access to deeply nested fields, and
    possibly also ensure that some critical fields exist, even if the values
    are empty, for some collections.

    Args:
        collection: The name of the collection to which the record belongs.
        record: A mapping representing a JSON record.
        version: The Pure API version, without the decimal point.

    Returns:
        A transformed record.

    Raises:
        common.PureAPIInvalidCollectionError: If the collection name is
            invalid for the given API version.
        common.PureAPIInvalidVersionError: If the API version number
            is unrecognized.
    '''
    transformer = transformer_for(collection=collection, version=version)
    return transformer(record)

import os
from addict import Dict
from . import *
#from .exceptions import PureAPIUnknownFamilyError, PureAPIUnknownVersionError

pure_api_version = os.environ.get('PURE_API_VERSION')

def default(record):
    d = Dict(record)
    return d

def change(record):
    d = Dict(record)
    return d
change_516 = change

def external_organisation(record):
    d = Dict(record)
    d.info.setdefault('previousUuids', [])
    d.setdefault('pureId', None)
    return d
external_organisation_516 = external_organisation

def external_person(record):
    d = Dict(record)
    d.info.setdefault('previousUuids', [])
    d.setdefault('name', Dict())
    d.name.setdefault('firstName', None)
    d.name.setdefault('lastName', None)
    return d
external_person_516 = external_person

def organisational_unit(record):
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
organisational_unit_516 = organisational_unit

def person(record):
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
person_516 = person

def research_output(record):
    d = Dict(record)
    d.setdefault('electronicVersions', [])
    d.info.setdefault('additionalExternalIds', [])
    d.info.setdefault('previousUuids', [])
    d.setdefault('volume', None)
    d.setdefault('journalNumber', None)
    d.setdefault('pages', None)
    d.setdefault('totalScopusCitations', None)
    return d
research_output_516 = research_output

@validate_collection
def transformer_for(*, collection, version=None):
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

def transform(collection, record, *, version=None):
    transformer = transformer_for(collection=collection, version=version)
    return transformer(record)

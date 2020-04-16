from addict import Dict
from .exceptions import PureAPIResponseException, PureAPIResponseKeyError

def change(dictionary):
    d = Dict(dictionary)
    return d

def external_organisation(dictionary):
    d = Dict(dictionary)
    d.info.setdefault('previousUuids', [])
    d.setdefault('pureId', None)
    return d

def external_person(dictionary):
    d = Dict(dictionary)
    d.info.setdefault('previousUuids', [])
    d.setdefault('name', Dict())
    d.name.setdefault('firstName', None)
    d.name.setdefault('lastName', None)
    return d

def organisational_unit(dictionary):
    d = Dict(dictionary)
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

def person(dictionary):
    d = Dict(dictionary)
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

def research_output(dictionary):
    d = Dict(dictionary)
    d.setdefault('electronicVersions', [])
    d.info.setdefault('additionalExternalIds', [])
    d.info.setdefault('previousUuids', [])
    d.setdefault('volume', None)
    d.setdefault('journalNumber', None)
    d.setdefault('pages', None)
    d.setdefault('totalScopusCitations', None)
    return d

def transformer_for_family(family):
    return {
        'changes': 'change',
        'external-organisations': 'external_organisation',
        'external-persons': 'external_person',
        'organisational-units': 'organisational_unit',
        'persons': 'person',
        'research-outputs': 'research_output',
    }.get(family, None)

def transform(family, dictionary):
    transformer = transformer_for_family(family)
    if (transformer == None):
        raise PureAPIResponseKeyError('Unrecognized family "{}"'.format(family))
    return globals()[transformer_for_family(family)](dictionary)

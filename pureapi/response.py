from addict import Dict

def change(dictionary):
  d = Dict(dictionary)
  return d

def external_organisation(dictionary):
  d = Dict(dictionary)
  d.setdefault('pureId', None)
  return d

def external_person(dictionary):
  d = Dict(dictionary)
  return d

def organisational_unit(dictionary):
  d = Dict(dictionary)
  return d

def person(dictionary):
  d = Dict(dictionary)
  return d

def research_output(dictionary):
  d = Dict(dictionary)
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
    raise NoSuchFamilyError('Unrecognized family "{}"'.format(family))
  return globals()[transformer_for_family(family)](dictionary)

class Error(Exception):
  pass

class NoSuchFamilyError(Error):
  def __init__(self, message):
    self.message = message

from addict import Dict

def organisational_unit(dictionary):
  ou = Dict(dictionary)
  return ou

def person(dictionary):
  p = Dict(dictionary)
  return p

def research_output(dictionary):
  ro = Dict(dictionary)
  ro.setdefault('totalScopusCitations', None)
  return ro

def transformer_for_family(family):
  return {
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

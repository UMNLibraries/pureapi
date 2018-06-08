from pureapi import response
from addict import Dict
import pytest

def test_person():
  p = response.person({})
  assert isinstance(p, Dict)
  assert p.name.firstName == None
  assert p.name.lastName == None
  assert p.externalId == None
  assert p.scopusHIndex == None
  assert p.orcid == None

  p2 = response.person({'name': {'lastName': 'Valiullin'}})
  assert p2.name.firstName == None
  assert p2.name.lastName == 'Valiullin'

def test_external_person():
  p = response.external_person({})
  assert isinstance(p, Dict)
  assert p.name.firstName == None
  assert p.name.lastName == None

  p2 = response.external_person({'name': {'firstName': 'Darth', 'lastName': 'Vader'}})
  assert p2.name.firstName == 'Darth'
  assert p2.name.lastName == 'Vader'

def test_organisational_unit():
  ou = response.organisational_unit({})
  assert isinstance(ou, Dict)
  assert ou.externalId == None
  assert ou.parents[0].uuid == None

def test_external_organisation():
  eo = response.external_organisation({})
  assert isinstance(eo, Dict)
  assert eo.pureId == None

def test_research_output():
  ro1_citation_count = 100
  ro1 = response.research_output({'totalScopusCitations': ro1_citation_count})
  assert isinstance(ro1, Dict)
  assert ro1.totalScopusCitations == ro1_citation_count

  ro2_citation_count = None
  ro2 = response.research_output({})
  assert isinstance(ro2, Dict)
  assert ro2.totalScopusCitations == ro2_citation_count

def test_transformer_for_family():
  assert response.transformer_for_family('research-outputs') == 'research_output'
  assert response.transformer_for_family('no-such-family') == None

def test_transform():
  citation_count = None
  ro = response.transform('research-outputs', {})
  assert isinstance(ro, Dict)
  assert ro.totalScopusCitations == citation_count

def test_transform_error():
  with pytest.raises(response.NoSuchFamilyError):
    response.transform('no-such-family', {})

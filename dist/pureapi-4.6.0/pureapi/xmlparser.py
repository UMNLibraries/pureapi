import xml.etree.ElementTree as et
import re

def records(xml):
  root = et.fromstring(xml)
  return root.findall('result/content')

def organisation(record):
  org = {
    'pure_uuid': record.attrib['uuid'],
    'parent_pure_uuid': None,
    'parent_pure_id': None,
    'type': record.find("./typeClassification/term/localizedString[@locale='en_US']").text.lower(),
  }

  # Hard-coded for now. Will need to change once we start importing external orgs.
  org['pure_internal'] = 'Y'

  # These fields will exist only for internal orgs:
  pure_id_elem = record.find("./external/secondarySource[@source='synchronisedOrganisation']")
  org['pure_id'] = pure_id_elem.attrib['source_id'] if pure_id_elem is not None else None

  name_en_elem = record.find("./name/localizedString[@locale='en_US']")
  org['name_en'] = name_en_elem.text if name_en_elem is not None else None

  name_variant_elem = record.find("./nameVariant/classificationDefinedFieldExtension/value/localizedString[@locale='en_US']")
  org['name_variant_en'] = name_variant_elem.text if name_variant_elem is not None else None

  url_elem = record.find("./webAddresses/classificationDefinedFieldExtension/value/localizedString[@locale='en_US']")
  org['url'] = url_elem.text if url_elem is not None else None

  parent_org_elem = record.find('./organisations/organisation')
  if parent_org_elem is not None:
    org['parent_pure_uuid'] = parent_org_elem.attrib['uuid']
    parent_pure_id_elem = parent_org_elem.find("./external/secondarySource[@source='synchronisedOrganisation']")
    org['parent_pure_id'] = parent_pure_id_elem.attrib['source_id'] if parent_pure_id_elem is not None else None

  return org

def external_organisation(external_org_elem):
  return {
    'pure_uuid': external_org_elem.attrib['uuid'],
    # Pure doesn't specify that this will be in English, so maybe a bad assumption:
    'name_en': external_org_elem.find('./name').text,
    'type': external_org_elem.find("./typeClassification/term/localizedString[@locale='en_US']").text.lower(),
    'pure_internal': 'N',

    # Pure doesn't give us these fields for external orgs, so we just set them all to None:
    'name_variant_en': None,
    'pure_id': None,
    'parent_pure_id': None,
    'parent_pure_uuid': None,
    'url': None
  }

def organisation_association(org_assoc_elem):
  org_assoc = {}         

  employment_type_elem = org_assoc_elem.find("./employmentType/term/localizedString[@locale='en_US']")
  org_assoc['employment_type'] = employment_type_elem.text if employment_type_elem is not None else None

  org_assoc['organisation'] = organisation(org_assoc_elem.find('./organisation'))

  start_date_elem = org_assoc_elem.find('./period/startDate')
  org_assoc['start_date'] = start_date_elem.text if start_date_elem is not None else None

  end_date_elem = org_assoc_elem.find('./period/endDate')
  org_assoc['end_date'] = end_date_elem.text if end_date_elem is not None else None

  # This element seems to exist only for primary associations.
  primary_assoc_elem = org_assoc_elem.find('./primaryAssociation')
  org_assoc['primary_association'] = primary_assoc_elem.text if primary_assoc_elem is not None else 'false'

  return org_assoc

def staff_organisation_association(staff_org_assoc_elem):
  staff_org_assoc = {}         

  employment_type_elem = staff_org_assoc_elem.find("./employmentType/term/localizedString[@locale='en_US']")
  staff_org_assoc['employment_type'] = employment_type_elem.text if employment_type_elem is not None else None

  staff_org_assoc['organisation'] = organisation(staff_org_assoc_elem.find('./organisation'))

  start_date_elem = staff_org_assoc_elem.find('./period/startDate')
  staff_org_assoc['start_date'] = start_date_elem.text if start_date_elem is not None else None

  end_date_elem = staff_org_assoc_elem.find('./period/endDate')
  staff_org_assoc['end_date'] = end_date_elem.text if end_date_elem is not None else None

  # This element seems to exist only for primary associations.
  primary_assoc_elem = staff_org_assoc_elem.find('./primaryAssociation')
  staff_org_assoc['primary_association'] = primary_assoc_elem.text if primary_assoc_elem is not None else 'false'

  job_description_elem = staff_org_assoc_elem.find('./jobDescription')
  staff_org_assoc['job_description'] = job_description_elem.text if job_description_elem is not None else None

  return staff_org_assoc

# Don't know why Pure has so many repeated organisation-association elements.
# This one is a little different than the others, so had to use a different method,
# with a different name, for it.
def associated_organisation(assoc_org_elem):
  assoc_org = {
    'external': assoc_org_elem.find('./external').text,
    'organisation': organisation(assoc_org_elem.find('./organisation')),
  }         

  hidden_elem = assoc_org_elem.find('./hidden')
  assoc_org['hidden'] = hidden_elem.text if hidden_elem is not None else None

  return assoc_org

def person(person_elem):
  person = {
    'pure_uuid': person_elem.attrib['uuid'],

    # We default to internal. Parent elements will have context to set it otherwise.
    'pure_internal': 'Y',

    # Defaults for UMN-external persons:
    'emplid': None,
    'internet_id': None,
    'hindex': None,
    'scopus_id': None,
    'organisation_associations': [],
    'staff_organisation_associations': [],
  }

  first_name_elem = person_elem.find('./name/firstName')
  person['first_name'] = first_name_elem.text if first_name_elem is not None else None

  last_name_elem = person_elem.find('./name/lastName')
  person['last_name'] = last_name_elem.text if last_name_elem is not None else None

  emplid_elem = person_elem.find('./employeeId')
  person['emplid'] = emplid_elem.text if emplid_elem is not None else None

  for link_id_elem in person_elem.findall('./linkIdentifiers/linkIdentifier/linkIdentifier'):
    if re.match('umn:', link_id_elem.text):
      # Pure prefixes internet IDs with 'umn:', which we remove:
      person['internet_id'] = link_id_elem.text[4:]
      # Should be only one internet ID:
      break

  # TODO: Will we always have an hindex for internal persons?
  hindex_elem = person_elem.find('./hIndex')
  person['hindex'] = hindex_elem.attrib['hIndexTotal'] if hindex_elem is not None else None

  scopus_id_elem = person_elem.find("./external/secondarySource[@source='Scopus']")
  person['scopus_id'] = scopus_id_elem.attrib['source_id'] if scopus_id_elem is not None else None

  pure_id_elem = person_elem.find("./external/secondarySource[@source='synchronisedPerson']")
  person['pure_id'] = pure_id_elem.attrib['source_id'] if pure_id_elem is not None else None

  for org_assoc_elem in person_elem.findall('./organisationAssociations/organisationAssociation'): 
    person['organisation_associations'].append(organisation_association(org_assoc_elem))

  for staff_org_assoc_elem in person_elem.findall('./staffOrganisationAssociations/staffOrganisationAssociation'): 
    person['staff_organisation_associations'].append(staff_organisation_association(staff_org_assoc_elem))

  return person

def person_association(person_assoc_elem):
  person_assoc = {
    'person_role': person_assoc_elem.find('./personRole/term/localizedString').text.lower(),
    # This will be set by the calling code (e.g. publication()):
    'ordinal': None,
    'organisation_associations': [],
  }

  first_name_elem = person_assoc_elem.find('./name/firstName')
  person_assoc['first_name'] = first_name_elem.text if first_name_elem is not None else None

  last_name_elem = person_assoc_elem.find('./name/lastName')
  person_assoc['last_name'] = last_name_elem.text if last_name_elem is not None else None

  external_org_elem = person_assoc_elem.find('./externalOrganisation') 
  person_assoc['external_organisation'] = external_org_elem.text if external_org_elem is not None else None

  internal_person_elem = person_assoc_elem.find('./person')
  external_person_elem = person_assoc_elem.find('./externalPerson')
  if internal_person_elem is not None:
    person_assoc['person'] = person(internal_person_elem)
  elif external_person_elem is not None:
    person_assoc['person'] = person(external_person_elem)
    person_assoc['person']['pure_internal'] = 'N'
  else:
    print('No person found for person_association: ' + str(person_assoc))
  
  for assoc_org_elem in person_assoc_elem.findall('./organisations/association'): 
    person_assoc['organisation_associations'].append(associated_organisation(assoc_org_elem))

  hidden_elem = person_assoc_elem.find('./hidden')
  person_assoc['hidden'] = hidden_elem.text if hidden_elem is not None else None

  return person_assoc

# Right now, this handles only ContributionToJournalType records.
def publication(pub_elem):
  publication = {  
    'pure_uuid': pub_elem.attrib['uuid'],
    # Hard-coded for now:
    'type': 'article-journal',
    'title': pub_elem.find('./title').text,
    'container_title': pub_elem.find('./journal/title/string').text,
    'person_associations': [],
    'organisation_associations': [],
    'associated_external_organisations': [],
  }

  scopus_id_elem = pub_elem.find("./external/secondarySource[@source='Scopus']")
  publication['scopus_id'] = scopus_id_elem.attrib['source_id'] if scopus_id_elem is not None else None

  pmid_elem = pub_elem.find("./external/secondarySource[@source='PubMed']")
  publication['pmid'] = pmid_elem.attrib['source_id'] if pmid_elem is not None else None

  # Seems there may be more than one of these in the Pure pub_elem, but we just use the 
  # first one for now.
  doi_elem = pub_elem.find('./dois/doi/doi')
  publication['doi'] = doi_elem.text if doi_elem is not None else None

  issn_elem = pub_elem.find('./journal/issn/string')
  publication['issn'] = issn_elem.text if issn_elem is not None else None

  volume_elem = pub_elem.find('./volume')
  publication['volume'] = volume_elem.text if volume_elem is not None else None

  issue_elem = pub_elem.find('./journalNumber')
  publication['issue'] = issue_elem.text if issue_elem is not None else None

  pages_elem = pub_elem.find('./pages')
  publication['pages'] = pages_elem.text if pages_elem is not None else None

  # TODO: So far, lots of pub_elems are missing this data. Is it missing from all of them?
  citation_total_elem = pub_elem.find('./citations/citationTotal')
  publication['citation_total'] = int(citation_total_elem.text) if citation_total_elem is not None else None

  year = pub_elem.find('./publicationDate/year').text
  issued_precision = 366
  month = '01'
  day = '01'
  month_elem = pub_elem.find('./publicationDate/month')
  if (month_elem is not None):
    month = month_elem.text
    if len(month) == 1:
      month = '0' + month
    issued_precision = 31
  day_elem = pub_elem.find('./publicationDate/day')
  if (day_elem is not None):
    day = day_elem.text
    if len(day) == 1:
      day = '0' + day
    issued_precision = 1
  publication['issued'] = {}
  publication['issued']['date_parts'] = [int(year), int(month), int(day)]
  publication['issued']['literal'] = '-'.join([year, month, day])
  publication['issued_precision'] = issued_precision

  person_ordinal = 0
  for person_assoc_elem in pub_elem.findall('./persons/personAssociation'):
    person_assoc = person_association(person_assoc_elem)
    person_assoc['ordinal'] = person_ordinal
    publication['person_associations'].append(person_assoc)
    person_ordinal = person_ordinal + 1

  for assoc_org_elem in pub_elem.findall('./organisations/association'): 
    publication['organisation_associations'].append(associated_organisation(assoc_org_elem))

  for external_org_elem in pub_elem.findall('./associatedExternalOrganisations/externalOrganisation'):
    publication['associated_external_organisations'].append(external_organisation(external_org_elem))

  publication['owner_organisation'] = organisation(pub_elem.find('./owner'))

  return publication

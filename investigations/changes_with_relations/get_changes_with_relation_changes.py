import dotenv_switch.auto
from datetime import date, timedelta
import sys

from pureapi import client

api_version = sys.argv[1]
client_config = client.Config(version=api_version)

family_system_names = [
  'Journal',
  'ExternalOrganisation',
  'ExternalPerson',
  'Organisation',
  'Person',
  'ResearchOutput',
]

def required_fields_exist(api_record):
    for field in ['uuid','familySystemName','version','changeType','relationChanges']:
        if field not in api_record:
            return False
    return True

yesterday = date.today() - timedelta(days=1)
for api_record in client.get_all_changes_transformed(yesterday.isoformat(), config=client_config):

    if api_record.familySystemName not in family_system_names:
        continue
    if not required_fields_exist(api_record):
        continue
    print(api_record)

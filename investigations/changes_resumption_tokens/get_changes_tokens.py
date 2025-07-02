from dotenv import load_dotenv
load_dotenv()
from datetime import date, timedelta
import sys

from pureapi import client

api_version = sys.argv[1]
client_config = client.Config(version=api_version)

response_num = 0
yesterday = date.today() - timedelta(days=1)
for response in client.get_all_changes(yesterday.isoformat(), config=client_config):
    print(f'{response_num=}')
    response_num += 1
#    rjson = response.json()
#    print(f"{rjson['moreChanges']=}")
#    if 'resumptionToken' in rjson:
#        print(f"{rjson['resumptionToken']=}")
#    if 'navigationLinks' in rjson:
#        print(f"{rjson['navigationLinks']=}")

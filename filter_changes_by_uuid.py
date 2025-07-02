from dotenv import load_dotenv
load_dotenv()
#from datetime import date, timedelta
from datetime import datetime
import json
import sys

from pureapi import client

#yesterday = date.today() - timedelta(days=1)
start_date_str = sys.argv[1]
start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#print(start_date)

uuid = sys.argv[2]
client_config = client.Config()

uuid_found = False
for response in client.get_all_changes(start_date.isoformat(), config=client_config):
    rjson = response.json()
    for item in rjson['items']:
        if item['uuid'] == uuid:
            uuid_found = True
            print(json.dumps(item))
            break
    if uuid_found:
        break
if not uuid_found:
    print(f'{uuid} not found')

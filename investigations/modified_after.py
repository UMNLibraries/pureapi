from dotenv import load_dotenv
load_dotenv()
#from datetime import date, timedelta
from datetime import datetime
import json
import sys

from pureapi import client

#yesterday = date.today() - timedelta(days=1)
start_date_str = sys.argv[1]
#start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#print(start_date)

for response in client.get('persons', params={'size':1, 'offset':0, 'modifiedAfter':start_date_str}):
    print(response.decode('utf-8'))

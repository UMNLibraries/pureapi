from dotenv import load_dotenv
load_dotenv()
from pureapi import client
from pureapi.client import Config

persons_only_api_key = 'bd3c6de3-6af3-4bb6-bb88-f868d51eda34'

count = 0
for change in client.get_all_changes_transformed(start_date='2022-07-20', config=Config(key=persons_only_api_key)):
    print(change)
    if count > 10:
        break
    count += 1

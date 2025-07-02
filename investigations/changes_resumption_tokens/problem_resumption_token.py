from dotenv import load_dotenv
load_dotenv()
from pureapi import client

#r = client.get('changes/eyJzZXF1ZW5jZU51bWJlciI6MTExMjl9=')
#r = client.get('changes/eyJzZXF1ZW5jZU51bWJlciI6MTExMjl9')
#print(r.json())
#r = client.get('changes/2022-06-28T00:00:00')
r = client.get('changes/2022-07-20')
first_changeset = r.json()
print(first_changeset)
token = first_changeset['resumptionToken']
while (token):
    r = client.get('changes/' + token)
    changeset = r.json()
    print(changeset)
    if 'resumptionToken' in changeset:
        token = changeset['resumptionToken']
    else:
        token = None

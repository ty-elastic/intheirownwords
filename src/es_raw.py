import json 
import requests
import urllib3
urllib3.disable_warnings()
import os

REQUEST_HEADERS = {'user-agent': 'intheirownwords/0.0.1', 'content-type': 'application/json'}

def search(index, query, fields, size=1, rank=None, source=False):
    
    merged = query
    merged.update(query)
    merged.update({"fields": fields})
    merged.update({"size": size})
    merged.update({"_source": source})
    if rank is not None:
        merged.update({"rank": rank})

    requestURL = f"https://{os.getenv('ES_ENDPOINT')}:443/{index}/_search"

    resp = requests.get(requestURL,
                    json=merged,
                    auth=(os.getenv('ES_USER'), os.getenv('ES_PASS')),
                    verify=False,
                    headers=REQUEST_HEADERS)
    resp = resp.json()
    
    #print(json.dumps(r , sort_keys = True, indent = 2, ensure_ascii = False))
    return resp
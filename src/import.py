import es_clauses
from datetime import datetime
import requests

def import_old():
    origins = es_clauses.get_origins()

    for origin in origins:
        projects = es_clauses.get_projects(origin)
        for project in projects:
            #print(project)

            u = {}
            u['media_url'] = project['media_url']
            u['source_url'] = project['source_url']
            u['title'] = project['title']
            u['date'] = project['date'][0:10]
            u['kind'] = project['kind']
            u['origin'] = project['origin']
            u['save_frames'] = False
            print(u)

            #u['local_path'] = "ingest/acdc.mp4"
            
            response = requests.post("http://127.0.0.1:8502/import", json=u)
            print(response)
            break


import_old()
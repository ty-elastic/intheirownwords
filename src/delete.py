import storage
import es_clauses
import es_voices
import es_origins

def delete_project(project_id):
    storage.delete_project(project_id)
    es_clauses.delete_project(project_id)

def delete_origin(origin):
    origin_rec = es_origins.get_origin(origin)

    projects = es_clauses.get_projects(origin)
    for project in projects:
        delete_project(project['project_id'])
    es_voices.delete_voices(origin)
    es_origins.delete_origin(origin)
    if 'logo_url' in origin_rec:
        storage.delete_logo(origin_rec['logo_url'])
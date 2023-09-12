from elasticsearch import Elasticsearch, helpers
import os
import es_helpers
from hashlib import sha512
import storage

ORIGINS_INDEX="origins"

BASE_URL = os.getenv('BASE_URL')

def add_origin(origin_id, origin, logo_url, homepage_url, media_kinds, results_size):

    print(media_kinds)

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:

        res = es.index(
            index=ORIGINS_INDEX,
            id=origin_id,
            document={
                'origin': origin,
                'logo_url': logo_url,
                'homepage_url': homepage_url,
                'kinds': media_kinds,
                'results.size': results_size
            })
        result = dict(res)
        return result['_id']

def get_origins():
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:

        fields = ["origin"]
        resp = es.search(index=ORIGINS_INDEX,
                            fields=fields,
                            size=100,
                            sort=[{'origin': {'order': 'asc'}}],
                            source=False)
        origins = []
        for origin in resp['hits']['hits']:
            doc = es_helpers.strip_field_arrays(origin['fields'])
            origins.append(doc['origin'])
        #print(origins)
        return origins
    
def hash_origin_id(origin):
    return str(sha512(origin.encode('utf-8')).hexdigest())

def delete_origin(origin):
    origin_id = hash_origin_id(origin)

    query = { "match": { "_id": origin_id } }

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        resp = es.delete_by_query(index=ORIGINS_INDEX,
                                query=query)
        #print(resp)

def get_origin(origin):
    if origin is None:
        return None

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        query = { "term": { "origin": origin } }

        fields = ["_id", "origin", "logo_url", "homepage_url", "kinds", "results.size"]
        resp = es.search(index=ORIGINS_INDEX,
                            query=query,
                            fields=fields,
                            size=100,
                            source=False)
        if len(resp['hits']['hits']) > 0:
            body = resp['hits']['hits'][0]['fields']
            doc = es_helpers.strip_field_arrays(body)
            if 'kinds' in doc:
                if not isinstance(doc['kinds'], list):
                    doc['kinds'] = [doc['kinds']]
            else:
                doc['kinds'] = []
            if not 'results.size' in doc:
                doc['results.size'] = 1
            if 'logo_url' in doc:
                logo_url = storage.get_signed_url(doc['logo_url'][1:])
                if logo_url is not None:
                    doc['logo_url'] = logo_url
                else:
                    doc['logo_url'] = BASE_URL + doc['logo_url']
            #print(doc)
            return doc
        return None
    
def update_origin(origin_id, origin, logo_url, homepage_url, media_kinds, results_size):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    # print(url)

    doc= {
                                'origin': origin,
                                'homepage_url': homepage_url,
                                'kinds': media_kinds,
                                'results.size': results_size
                             }
    if logo_url is not None:
        doc['logo_url'] = logo_url

    with Elasticsearch([url], verify_certs=True) as es:
        resp = es.update(index=ORIGINS_INDEX,
                         id=origin_id,
                         body={
                             "doc": doc
                         })
        #print(resp)
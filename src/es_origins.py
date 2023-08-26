from elasticsearch import Elasticsearch, helpers
import os
import es_helpers
import s3
import job

ORIGINS_INDEX="origins"

def upload_logo(uploaded_file, origin_id):
    split_tup = os.path.splitext(uploaded_file.name)
    input = os.path.join(job.INGEST_DIR, origin_id + split_tup[1])
    with open(input, "wb") as f:
        f.write(uploaded_file.getbuffer())
    logo_url = s3.upload_logo(input)
    os.remove(input)
    return logo_url

def add_origin(origin_id, origin, logo_url, homepage_url, media_kinds, results_size):

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
                            source=False)
        origins = []
        for origin in resp['hits']['hits']:
            doc = es_helpers.strip_field_arrays(origin['fields'])
            origins.append(doc['origin'])
        print(origins)
        return origins

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
            return doc
        return None
    
def update_origin(origin_id, origin, logo_url, homepage_url, media_kinds, results_size):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    # print(url)

    with Elasticsearch([url], verify_certs=True) as es:
        resp = es.update(index=ORIGINS_INDEX,
                         id=origin_id,
                         body={
                             "doc": {
                                'origin': origin,
                                'logo_url': logo_url,
                                'homepage_url': homepage_url,
                                'kinds': media_kinds,
                                'results.size': results_size
                             }
                         })
        print(resp)
from elasticsearch import Elasticsearch, helpers
import os
import es_helpers

ORIGINS_INDEX="origins"

def add_origin(origin, logo_url, homepage_url):

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:

        res = es.index(
            index=ORIGINS_INDEX,
            document={
                'origin': origin,
                'logo_url': logo_url,
                'homepage_url': homepage_url
            })
        result = dict(res)
        return result['_id']

def get_origin(origin):

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        query = { "term": { "origin": origin } }

        fields = ["origin", "logo_url", "homepage_url"]
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
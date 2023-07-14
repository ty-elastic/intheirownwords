from elasticsearch import Elasticsearch, helpers
import os
import batteries

VOICES_INDEX = "voices"
VOICE_CONFIDENCE_THRESHOLD = 0.85

def lookup_speaker_by_id(speaker_id):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        query = {
            "match":{
                "_id": speaker_id
            }
        }


        fields = ["_id", "speaker.name", "speaker.title", "speaker.company", "speaker.email"]
        resp = es.search(index=VOICES_INDEX,
                            query=query,
                            fields=fields,
                            size=1,
                            source=False)

        print(resp)
        if 'fields' in resp['hits']['hits'][0]:
            body = resp['hits']['hits'][0]['fields']
            return batteries.strip_field_arrays(body)
        else:
            return {}

def lookup_speaker(query_embedding):

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:

        knn = {
                "field": "voice_vector",
                "k": 2,
                "num_candidates": 10,
                "query_vector": query_embedding
            }

        result = es.search(
                index=VOICES_INDEX,
                knn=knn,
                size=1,
            )
        #print(result)
        if len(result['hits']['hits']) > 0:
            if result['hits']['hits'][0]['_score'] > VOICE_CONFIDENCE_THRESHOLD:
                return result['hits']['hits'][0]['_id']
        return None

def add_speaker(project, query_embedding, example_url, example_start, example_end):

    if project['enable_write']:
        url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
        with Elasticsearch([url], verify_certs=True) as es:

            res = es.index(
                index=VOICES_INDEX,
                document={
                    'example.url': example_url,
                    'example.start': example_start,
                    'example.end': example_end,
                    'voice_vector': query_embedding
                })
            result = dict(res)
            return result['_id']
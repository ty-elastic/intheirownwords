from elasticsearch import Elasticsearch, helpers
import os
import es_helpers

VOICES_INDEX = "voices"
VOICE_CONFIDENCE_THRESHOLD = 0.85

def get_speakers(origin):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        query = { "term": { "origin": origin } }

        fields = ["_id", "speaker.name", "speaker.title",
                  "speaker.company", "speaker.email"]
        resp = es.search(index=VOICES_INDEX,
                            query=query,
                            fields=fields,
                            size=100,
                            source=False)
        #print(resp)
        speakers = []
        for voice in resp['hits']['hits']:
            doc = es_helpers.strip_field_arrays(voice['fields'])
            if 'speaker.name' in doc:
                speakers.append(doc)
        print(speakers)
        return speakers

def get_unassigned_voices(origin):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"

    with Elasticsearch([url], verify_certs=True) as es:

        query = {
            "bool": {
                "must_not": {
                    "exists": {
                        "field": "speaker.name"
                    }
                }
            }
        }

        if origin is not None:
            query["bool"]["filter"] = {"term": {"origin": origin}}

        fields = ["_id", "example.end", "example.start",
                  "example.url", "example.source_url"]
        resp = es.search(index=VOICES_INDEX,
                         query=query,
                         fields=fields,
                         source=False)

        # print(resp)
        docs = []
        for voice in resp['hits']['hits']:
            doc = es_helpers.strip_field_arrays(voice['fields'])
            docs.append(doc)
        # print(docs)
        return docs


def update_speaker(speaker_id, speaker_name, speaker_title, speaker_company, speaker_email):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    # print(url)
    with Elasticsearch([url], verify_certs=True) as es:
        resp = es.update(index=VOICES_INDEX,
                         id=speaker_id,
                         body={
                             "doc": {
                                 'speaker.name': speaker_name,
                                 'speaker.title': speaker_title,
                                 'speaker.company': speaker_company,
                                 'speaker.email': speaker_email
                             }
                         })
        print(resp)


def lookup_speaker_by_id(speaker_id):

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"

    with Elasticsearch([url], verify_certs=True) as es:
        query = {
            "match": {
                "_id": speaker_id
            }
        }

        fields = ["_id", "speaker.name", "speaker.title",
                  "speaker.company", "speaker.email"]
        resp = es.search(index=VOICES_INDEX,
                         query=query,
                         fields=fields,
                         size=1,
                         source=False)

        print(resp)
        if 'fields' in resp['hits']['hits'][0]:
            body = resp['hits']['hits'][0]['fields']
            return es_helpers.strip_field_arrays(body)
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
        # print(result)
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
                    'example.source_url': project['source_url'],
                    'origin': project['origin'],
                    'voice_vector': query_embedding
                })
            result = dict(res)
            return result['_id']

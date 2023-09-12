from es_bulk import bulkLoadIndexPipeline
from elasticsearch import Elasticsearch, helpers
from elasticsearch.client import MlClient
import es_raw
import os
import es_voices
import es_helpers
import dateutil.parser
import yake
import es_ml
import storage

METHOD_RRF="RRF"
METHOD_HYBRID="Hybrid"

SEARCH_METHOD = METHOD_HYBRID
CLAUSES_INDEX = "clauses"
CLAUSES_PIPELINE = "clauses-embeddings"
CLAUSE_TEXT_BOOST = 1
CLAUSE_KEYWORD_BOOST = 0
CLAUSE_CONFIDENCE_THRESHOLD = 2

MIN_QA_CONFIDENCE_THRESHOLD = 0.01

def add_clauses(project):
    batch = []
    print(f"uploading {len(project['clauses'])} clauses...")
    for clause in project['clauses']:
        #print(clause)
        batch.append(clause)
        if len(batch) >= 100:
            bulkLoadIndexPipeline(batch,CLAUSES_INDEX,CLAUSES_PIPELINE)
            batch = []
    bulkLoadIndexPipeline(batch,CLAUSES_INDEX,CLAUSES_PIPELINE)

def delete_project(project_id):
    query = { "match": { "project_id": project_id } }

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        resp = es.delete_by_query(index=CLAUSES_INDEX,
                                query=query)
        print(resp)

def extract_keywords(search_text):
    kw_extractor = yake.KeywordExtractor()
    keywords = kw_extractor.extract_keywords(search_text)
    #print("KEY", keywords)
    if len(keywords) > 0:
        return keywords[0][0]
    return None

def get_project(project_id):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        query = { "term": { "project_id": project_id } }

        fields = ["kind", "origin", "date", "title", "media.url", "media_url", "source_url"]
        resp = es.search(index=CLAUSES_INDEX,
                            query=query,
                            fields=fields,
                            size=1,
                            source=False)
        #print(resp)
        if len(resp['hits']['hits']) > 0:
            body = resp['hits']['hits'][0]['fields']
            project = es_helpers.strip_field_arrays(body)
            #print (project)
            return project
        return None

def get_projects(origin):
    if origin is None:
        return []
    
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        # aggs = {
        #     "projects" : {
        #         "terms" : { "field" : "project_id",  "size" : 100 }
        #     }
        # }
        query = { "term": { "origin": origin }}
        collapse = {"field": "project_id"} 

        fields = ["project_id", "kind", "origin", "date", "date_uploaded", "title", "media.url",  "media_url", "source_url"]
        resp = es.search(index=CLAUSES_INDEX,
                            #aggs=aggs,

                            collapse=collapse,
                            query=query,
                            fields=fields,
                            size=100,
                            source=False)
        #print(resp)
        projects = []
        for hit in resp['hits']['hits']:
            #print(hit)
            project = es_helpers.strip_field_arrays(hit['fields'])
            projects.append(project)
        return projects

def get_voices(origin):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        aggs = {
            "speakers" : {
                "terms" : { "field" : "speaker.id",  "size" : 25 }
            }
        }

        query = { "term": { "origin": origin } }

        fields = ["speaker.id"]
        resp = es.search(index=CLAUSES_INDEX,
                            aggs=aggs,
                            fields=fields,
                            query=query,
                            size=1,
                            source=False)
        if len(resp['aggregations']['speakers']) > 0:
            speaker_ids = []
            for bucket in resp['aggregations']['speakers']['buckets']:
                speaker_ids.append(bucket['key'])
            #print(speaker_ids)
            return speaker_ids
        else:
            return None

def get_kinds(origin):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        aggs = {
            "kinds" : {
                "terms" : { "field" : "kind",  "size" : 100 }
            }
        }

        query = { "term": { "origin": origin } }

        fields = ["kind"]
        resp = es.search(index=CLAUSES_INDEX,
                            aggs=aggs,
                            fields=fields,
                            query=query,
                            size=1,
                            source=False)
        if len(resp['aggregations']['kinds']) > 0:
            media_kinds = []
            for bucket in resp['aggregations']['kinds']['buckets']:
                media_kinds.append(bucket['key'])
            #print(origins)
            return media_kinds
        else:
            return None
        
def get_origins():
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        aggs = {
            "origins" : {
                "terms" : { "field" : "origin",  "size" : 100, "order": { "_key" : "asc" } }
            }
        }

        fields = ["origin"]
        resp = es.search(index=CLAUSES_INDEX,
                            aggs=aggs,
                            fields=fields,
                            size=1,
                            source=False)
        if len(resp['aggregations']['origins']) > 0:
            origins = []
            for bucket in resp['aggregations']['origins']['buckets']:
                origins.append(bucket['key'])
            #print(origins)
            return origins
        else:
            return []


def make_hybrid_query(origin, search_text, keywords, text_boost, keyword_boost, speaker_id=None, kinds=None, start=None, stop=None):

    query_text = {
                "bool": { 
                    "must": [
                        {
                            "text_expansion": {
                                "text_elser.tokens": {
                                    "model_text": search_text,
                                    "model_id": ".elser_model_1",
                                    "boost": text_boost
                                }
                            }
                        },
                        { "term": { "origin": origin } }
                    ]
                }
            }
        
    if start != None or stop != None:
        date = {}
        if start != None:
            date['gte'] = start.strftime('%Y-%m-%d')
        if stop != None:
            date['lte'] = stop.strftime('%Y-%m-%d')       
        query_text['bool']['must'].append({
                        "range" : { "date" : date }
                    })   

    if speaker_id != None:
        query_text['bool']['must'].append({
                        "term" : { "speaker.id" : speaker_id }
                    })

    if kinds != None:
        query_text['bool']['must'].append({
                        "terms" : { "kind" : kinds }
                    })

    if keywords != None:
        query_text['bool']['should'] = [
                        {
                            "match": {
                                "text" : {
                                    "query": keywords,
                                    "boost": keyword_boost
                                }
                            }
                        },
                        {
                            "match": {
                                "scene.frame_text" : {
                                    "query": keywords,
                                    "boost": keyword_boost
                                }
                            }
                        }
                    ]


    #print(query_text)
    return query_text

def make_rrf_query(origin, search_text, keywords, speaker_id=None, kinds=None, start=None, stop=None):

    query_text = {
        "sub_searches": [
            {
                "query": {
                        "bool": {
                            "should": [
                                {
                                            "match": {
                                                "scene.frame_text": {
                                                    "query": keywords
                                                }
                                            }
                                }
                            ],
                            "must": [
                                { "term": { "origin": origin } }
                            ]
                        }
                    },
                    
            },
            {
                "query": {
                        "bool": {
                            "should": [
                                {

                                            "match": {
                                                "text": {
                                                    "query": keywords
                                                }
                                            }
                                }
                            ],
                            "must": [
                                { "term": { "origin": origin } }
                            ]

                        }
                    }
            },
            {
                
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "text_expansion": {
                                        "text_elser.tokens": {
                                            "model_text": search_text,
                                            "model_id": ".elser_model_1"
                                        }
                                    }
                                },
                                { "term": { "origin": origin } }
                            ]
                    }
                }
            }
        ]
    }

    if start != None or stop != None:
        date = {}
        if start != None:
            date['gte'] = start.strftime('%Y-%m-%d')
        if stop != None:
            date['lte'] = stop.strftime('%Y-%m-%d')
        for search in query_text['sub_searches']:
            if 'must' not in search['query']['bool']:
                search['query']['bool']['must'] = []
            search['query']['bool']['must'].append({
                            "range" : { "date" : date }
                        })   

    if speaker_id != None:
        for search in query_text['sub_searches']:
            if 'must' not in search['query']['bool']:
                search['query']['bool']['must'] = []
            search['query']['bool']['must'].append({
                                "term" : { "speaker.id" : speaker_id }
                        })   

    if kinds != None:
        for search in query_text['sub_searches']:
            if 'must' not in search['query']['bool']:
                search['query']['bool']['must'] = []
            search['query']['bool']['must'].append({
                            "terms" : { "kind" : kinds }
                        })

    rank =  {
            "rrf": {

            }
        }
    print(query_text)
    return query_text, rank
 

def find_clauses(origin, search_text, speaker_id=None, kinds=None, size=1, start=None, stop=None):
    size = 1 if size is None else size

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        fields = ["kind", "origin", "date", "title", "media.start", "media.end", "text", "media.url", "source_url", "scene.frame_url", "speaker.id", "scene.frame_text"]

        keywords = extract_keywords(search_text)

        # for now, always run hybrid to get scoring
        query = make_hybrid_query(origin, search_text, keywords, CLAUSE_TEXT_BOOST, CLAUSE_KEYWORD_BOOST, speaker_id=speaker_id, kinds=kinds, start=start, stop=stop)
        resp = es.search(index=CLAUSES_INDEX,
                        query=query,
                        fields=fields,
                        size=size,
                        source=False)
        print(resp)
        found = False
        for hit in resp['hits']['hits']:
            if hit['_score'] >= CLAUSE_CONFIDENCE_THRESHOLD:
                found = True
        if not found:
            return []


        if SEARCH_METHOD == METHOD_RRF and keywords != None:
            query, rank = make_rrf_query(origin, search_text, keywords, speaker_id=speaker_id, kinds=kinds, start=start, stop=stop)
            resp = es_raw.search(index=CLAUSES_INDEX,
                                query=query,
                                fields=fields,
                                size=size,
                                rank=rank,
                                source=False)
            print(resp)
            for hit in resp['hits']['hits']:
                hit['_score'] = CLAUSE_CONFIDENCE_THRESHOLD

        clauses = []
        for hit in resp['hits']['hits']:
            if hit['_score'] >= CLAUSE_CONFIDENCE_THRESHOLD:
                body = hit['fields']

                clause = es_helpers.strip_field_arrays(body)
                #clause['source.date'] = dateutil.parser.isoparse(clause['source.date'])

                media_url = storage.get_signed_url(clause['media.url'][1:])
                if media_url is not None:
                    clause['media.url'] = media_url
                    clause['media.url_http'] = True
                else:
                    clause['media.url_http'] = False

                voice = es_voices.lookup_speaker_by_id(body['speaker.id'][0])
                clause.update(voice)

                answer = es_ml.ask_question(clause['text'], search_text)
                if answer is not None and answer['prediction_probability'] >= MIN_QA_CONFIDENCE_THRESHOLD:
                    #start, stop = es_ml.find_text_that_answers_question(clause['text'], answer)
                    clause['answer.text'] = answer['predicted_value']
                    clause['answer.start'] = answer['start_offset']
                    clause['answer.stop'] = answer['end_offset']
                else:
                    clause['answer.start'] = 0
                    clause['answer.stop'] = 0

                clause['confidence'] = hit['_score']
                clauses.append(clause)
            else:
                print(f"ignoring={hit}")
        #print(clauses)
        return clauses
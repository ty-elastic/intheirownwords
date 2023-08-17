from es_bulk import bulkLoadIndexPipeline
from elasticsearch import Elasticsearch, helpers
from elasticsearch.client import MlClient
import es_raw
import os
import es_voices
import es_helpers
import dateutil.parser
import yake

METHOD_RRF="RRF"
METHOD_HYBRID="Hybrid"

CLAUSES_INDEX = "clauses"
CLAUSES_PIPELINE = "clauses-embeddings"
CLAUSE_TEXT_BOOST = 2
CLAUSE_KEYWORD_BOOST = 0
CLAUSE_CONFIDENCE_THRESHOLD = 15

def add_clauses(project):
    batch = []
    for clause in project['clauses']:
        print(clause)
        batch.append(clause)
        if len(batch) >= 100:
            bulkLoadIndexPipeline(batch,CLAUSES_INDEX,CLAUSES_PIPELINE)
            batch = []
    bulkLoadIndexPipeline(batch,CLAUSES_INDEX,CLAUSES_PIPELINE)

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

        fields = ["kind", "origin", "date", "title", "media_url", "source_url"]
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
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        aggs = {
            "projects" : {
                "terms" : { "field" : "project_id",  "size" : 100 }
            }
        }
        query = { "term": { "origin": origin } }

        fields = ["kind", "origin", "date", "title", "media_url", "source_url"]
        resp = es.search(index=CLAUSES_INDEX,
                            aggs=aggs,
                            query=query,
                            fields=fields,
                            size=100,
                            source=False)
        if len(resp['aggregations']['projects']) > 0:
            projects = []
            for bucket in resp['aggregations']['projects']['buckets']:
                project = get_project(bucket['key'])
                projects.append(project)
            #print(projects)
            return projects
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
            return None


def make_hybrid_query(origin, search_text, text_boost, keyword_boost, speaker_id=None, kind=None):
    keywords = extract_keywords(search_text)
    print(keywords)

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
                        }
                    ],
                    "filter": [{
                        "term" : { "origin" : origin }
                    }]
                }
            }
    
    if keywords != None:
        query_text['bool']['should'] = [
                        {
                            "match": {
                                "scene.frame_text" : {
                                    "query": keywords,
                                    "boost": keyword_boost
                                }
                            }
                        }
                    ]
    if speaker_id != None:
        query_text['bool']['filter'].append({
                        "term" : { "speaker.id" : speaker_id }
                    })

    if kind != None:
        query_text['bool']['filter'].append({
                        "term" : { "kind" : kind }
                    })

    #print(query_text)
    return query_text

def make_rrf_query(origin, search_text):
    keywords = extract_keywords(search_text)
    print(keywords)

    if keywords != None:

        query_text = {
            "sub_searches": [
                {
                    
                    "query": {
                            "bool": {
                                "must": {
                                "match": {
                                    "scene.frame_text": {
                                        "query": keywords
                                    }
                                }},
                                "filter": {
                                    "term" : { "origin" : origin }
                                }
                            }
                        }
                },
                {
                    
                        "query": {
                            "bool": {
                                "must": {
                                "text_expansion": {
                                    "text_elser.tokens": {
                                        "model_text": search_text,
                                        "model_id": ".elser_model_1"
                                    }
                                }},
                            "filter": {
                                "term" : { "origin" : origin }
                            }
                        }
                    }
                }
            ]
        }
  
        rank =  {
                "rrf": {

                }
            }
        return query_text, rank
    else:
        query_text = {
                "bool": { 
                    "must": [
                        {
                            "text_expansion": {
                                "text_elser.tokens": {
                                    "model_text": search_text,
                                    "model_id": ".elser_model_1"
                                }
                            }
                        }
                    ],
                    "filter": {
                        "term" : { "origin" : origin }
                    }
                }
        } 

        return query_text, None

def find_clauses(origin, search_text, method, speaker_id=None, kind=None):

    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:

        

        fields = ["kind", "origin", "date", "title", "start", "end", "text", "media_url", "source_url", "scene.frame_url", "speaker.id", "scene.frame_text"]

        if method == METHOD_RRF:
            query, rank = make_rrf_query(origin, search_text)
            resp = es_raw.search(index=CLAUSES_INDEX,
                                query=query,
                                fields=fields,
                                size=1,
                                rank=rank,
                                source=False)
            #print(resp)
            if len(resp['hits']['hits']) > 0:
                resp['hits']['hits'][0]['_score'] = CLAUSE_CONFIDENCE_THRESHOLD
        elif method == METHOD_HYBRID:
            query = make_hybrid_query(origin, search_text, CLAUSE_TEXT_BOOST, CLAUSE_KEYWORD_BOOST, speaker_id=speaker_id, kind=kind)
            resp = es.search(index=CLAUSES_INDEX,
                            query=query,
                            fields=fields,
                            size=1,
                            source=False)
            
        #print(resp)
        if len(resp['hits']['hits']) > 0:
            if resp['hits']['hits'][0]['_score'] >= CLAUSE_CONFIDENCE_THRESHOLD:
                body = resp['hits']['hits'][0]['fields']

                clause = es_helpers.strip_field_arrays(body)
                clause['date'] = dateutil.parser.isoparse(clause['date'])
            
                voice = es_voices.lookup_speaker_by_id(body['speaker.id'][0])
                clause.update(voice)
                #print (clause)

                return clause
        return None
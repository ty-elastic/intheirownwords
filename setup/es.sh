#!/bin/bash

Q_AND_A_MODEL="deepset__roberta-base-squad2"

git clone https://github.com/elastic/eland.git
docker build -t elastic/eland eland

set -o allexport
source ../env.vars
set +o allexport

ELASTICSEARCH_URL="https://${ES_USER}:${ES_PASS}@${ES_ENDPOINT}:443"
sudo docker run -it --rm elastic/eland \
    eland_import_hub_model \
      --url $ELASTICSEARCH_URL \
      --hub-model-id deepset/roberta-base-squad2 \
      --clear-previous \
      --start

curl -XPUT "$ELASTICSEARCH_URL/_ml/trained_models/.elser_model_1" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
{
  "input": {
	"field_names": ["text_field"]
  }
}'
curl -XPOST "$ELASTICSEARCH_URL/_ml/trained_models/.elser_model_1/deployment/_start?deployment_id=for_search" -H "kbn-xsrf: reporting"

curl -XDELETE "$ELASTICSEARCH_URL/clauses" -H "kbn-xsrf: reporting"
curl -XPUT "$ELASTICSEARCH_URL/clauses" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
{
 "mappings": {
   "properties": {
     "project_id": {
       "type": "keyword"
     }, 
     "media_url": {
       "type": "keyword"
     },
     "title": {
       "type": "text"
     },
     "date": {
       "type": "date"
     },
     "kind": {
       "type": "keyword"
     },
     "origin": {
       "type": "keyword"
     },
     
     "scene.start": {
       "type": "float"
     },
     "scene.end": {
       "type": "float"
     },
     "scene.frame_text": {
       "type": "text"
     },
     "scene.frame_url": {
       "type": "keyword"
     },
     "scene.frame_num": {
       "type": "integer"
     },
     
     "text": {
       "type": "text"
     },
     "text_elser.tokens": {
        "type": "rank_features" 
      },
      
     "speaker.id": {
       "type": "keyword"
     },
     
     "start": {
       "type": "float"
     },
     "end": {
       "type": "float"
     }
     
   }
 }
}'

curl -XDELETE "$ELASTICSEARCH_URL/_ingest/pipeline/clauses-embeddings" -H "kbn-xsrf: reporting"
curl -XPUT "$ELASTICSEARCH_URL/_ingest/pipeline/clauses-embeddings" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
{
 "description": "Clauses embedding pipeline",
 "processors": [
   {
      "inference": {
        "model_id": ".elser_model_1",
        "target_field": "text_elser",
        "field_map": { 
          "text": "text_field"
        },
        "inference_config": {
          "text_expansion": { 
            "results_field": "tokens"
          }
        }
      }
    }
 ],
 "on_failure": [
   {
     "set": {
       "description": "Index document to '\''failed-<index>'\''",
       "field": "_index",
       "value": "failed-{{{_index}}}"
     }
   },
   {
     "set": {
       "description": "Set error message",
       "field": "ingest.failure",
       "value": "{{_ingest.on_failure_message}}"
     }
   }
 ]
}'

curl -XDELETE "$ELASTICSEARCH_URL/voices" -H "kbn-xsrf: reporting"
curl -XPUT "$ELASTICSEARCH_URL/voices" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
{
 "mappings": {
   "properties": {
     "example.url": {
       "type": "keyword"
     },
     "example.source_url": {
       "type": "keyword"
     },

     "example.start": {
       "type": "float"
     },
     "example.stop": {
       "type": "float"
     },
     
     "speaker.name": {
       "type": "keyword"
     },
     "speaker.title": {
       "type": "keyword"
     },
     "speaker.company": {
       "type": "keyword"
     },
     "speaker.email": {
       "type": "keyword"
     },
     
     "voice_vector": {
       "type": "dense_vector",
       "dims": 192,
       "index": true,
       "similarity": "cosine"
     }
   }
 }
}'

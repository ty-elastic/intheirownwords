#!/bin/bash

models="false"
voices="false"
while getopts m:v: flag
do
    case "${flag}" in
        m) models="true";;
        v) voices="true";;
    esac
done
echo "models=$models"
echo "voices=$voices"

#Q_AND_A_MODEL="deepset/roberta-base-squad2"
Q_AND_A_MODEL="bert-large-uncased-whole-word-masking-finetuned-squad"

set -o allexport
source ../env.vars
set +o allexport

ELASTICSEARCH_URL="https://${ES_USER}:${ES_PASS}@${ES_ENDPOINT}:443"

if [ "$models" == "false" ]; then
  git clone https://github.com/elastic/eland.git
  docker build -t elastic/eland eland

  sudo docker run -it --rm elastic/eland \
      eland_import_hub_model \
        --url $ELASTICSEARCH_URL \
        --hub-model-id $Q_AND_A_MODEL \
        --clear-previous \
        --start

  curl -XPUT "$ELASTICSEARCH_URL/_ml/trained_models/.elser_model_1" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
  {
    "input": {
      "field_names": ["text_field"]
    }
  }'
  curl -XPOST "$ELASTICSEARCH_URL/_ml/trained_models/.elser_model_1/deployment/_start?deployment_id=for_search" -H "kbn-xsrf: reporting"
fi

echo "create origins"
curl -XDELETE "$ELASTICSEARCH_URL/origins" -H "kbn-xsrf: reporting"
curl -XPUT "$ELASTICSEARCH_URL/origins" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
{
"mappings": {
  "dynamic": "strict",
  "properties": {
    "origin": {
      "type": "keyword"
    }, 
    "logo_url": {
      "type": "keyword"
    },
    "homepage_url": {
      "type": "keyword"
    },
    "kinds": {
      "type": "keyword"
    },
    "results.size": {
        "type": "integer"
    }
  }
}
}'

echo "create clauses"
curl -XDELETE "$ELASTICSEARCH_URL/clauses" -H "kbn-xsrf: reporting"
curl -XPUT "$ELASTICSEARCH_URL/clauses" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
{
"mappings": {
  "dynamic": "strict",
  "properties": {
    "project_id": {
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
    "source_url": {
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
    "text_elser.model_id": {
        "type": "keyword" 
    },

    "speaker.id": {
      "type": "keyword"
    },
    
    "media.url": {
      "type": "keyword"
    },
    "media.start": {
      "type": "float"
    },
    "media.end": {
      "type": "float"
    },
    
    "date_uploaded": {
      "type": "date"
    },
    "persist_days": {
      "type": "integer"
    }

  }
}
}'

echo "create clauses-embeddings"
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

if [ "$voices" == "false" ]; then
  echo "create voices"
  curl -XDELETE "$ELASTICSEARCH_URL/voices" -H "kbn-xsrf: reporting"
  curl -XPUT "$ELASTICSEARCH_URL/voices" -H "kbn-xsrf: reporting" -H "Content-Type: application/json" -d'
  {
  "mappings": {
    "dynamic": "strict",
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
      "example.end": {
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
      "origin": {
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
fi
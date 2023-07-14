DELETE /clauses
PUT /clauses
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
}

DELETE _ingest/pipeline/clauses-embeddings
PUT _ingest/pipeline/clauses-embeddings
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
       "description": "Index document to 'failed-<index>'",
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
}

DELETE /voices
PUT /voices
{
 "mappings": {
   "properties": {
     "example.url": {
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
}

from elasticsearch import Elasticsearch, helpers
import os

BATCH_SIZE = 25  # Set your desired batch size here
RETRIES = 2

def batchify(docs, BATCH_SIZE):
    for i in range(0, len(docs), BATCH_SIZE):
        yield docs[i:i + BATCH_SIZE]

def bulkLoadIndexPipeline( json_docs, index_name,  pipeline):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:

        # doc_type = "_doc"

        # Create the index with the mapping if it doesn't exist
        # if not es.indices.exists(index=index_name):
        #     es.indices.create(index=index_name, body=mapping)

        batches = list(batchify(json_docs, BATCH_SIZE))

        for batch in batches:
            # Convert the JSON documents to the format required for bulk insertion
            bulk_docs = [
                {
                    "_op_type": "index",
                    "_index": index_name,
                    "_source": doc,
                    "pipeline": pipeline
                }
                for doc in batch
            ]

            # Perform bulk insertion
            for i in range(RETRIES):
                success, errors =  helpers.bulk(es, bulk_docs, raise_on_error=False, raise_on_exception=False)
                if errors:
                    for error in errors:
                        print(error)
                        # print(f"Error in document {error['_id']}: {error['index']['error']}")
                else:
                    print(f"Successfully inserted {success} documents.")
                    break
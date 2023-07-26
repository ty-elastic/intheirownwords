from elasticsearch.client import MlClient
from elasticsearch import Elasticsearch, helpers
import nltk.data

Q_AND_A_MODEL = "deepset__roberta-base-squad2"

def ask_question(context, question, strip=True):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        ml = MlClient(es)

        config = {"question_answering": {
            "question": question
        }}

        res = ml.infer_trained_model(model_id=Q_AND_A_MODEL, docs=[{ "text_field": context}], inference_config=config)
        print(res)
        if len(res['inference_results']) > 0:
            if strip:
                return res['inference_results'][0]['predicted_value']
            else:
                return res['inference_results'][0]

def find_sentence_that_answers_question(context, question, answer):
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = tokenizer.tokenize(context)
    candidates = []
    for sentence in sentences:
        if sentence.find(answer) != -1:
            print(sentence)
            return sentence

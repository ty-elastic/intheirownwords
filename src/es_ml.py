from elasticsearch.client import MlClient
from elasticsearch import Elasticsearch, helpers
from nltk.tokenize import PunktTokenizer
import nltk
import os
import re

#Q_AND_A_MODEL = "deepset__roberta-base-squad2"
#Q_AND_A_MODEL_CONFIG = "roberta"
Q_AND_A_MODEL = "bert-large-uncased-whole-word-masking-finetuned-squad"
Q_AND_A_MODEL_CONFIG = "bert"

nltk.download('punkt')
tokenizer = PunktTokenizer()

def ask_question(context, question):
    url = f"https://{os.getenv('ES_USER')}:{os.getenv('ES_PASS')}@{os.getenv('ES_ENDPOINT')}:443"
    with Elasticsearch([url], verify_certs=True) as es:
        ml = MlClient(es)

        config = {"question_answering": {
            "question": question,
            "tokenization": {
                Q_AND_A_MODEL_CONFIG: {
                    "truncate": "second",
                    "span": -1          
                    }
            }
        }}

        res = ml.infer_trained_model(model_id=Q_AND_A_MODEL, docs=[{ "text_field": context}], inference_config=config)
        print(res)
        if len(res['inference_results']) > 0:
            return res['inference_results'][0]

def find_sentence_that_answers_question(context, question, answer):
    sentences = split_sentences(context)
    candidates = []
    for i, sentence in enumerate(sentences):
        if sentence.find(answer) != -1:
            print(sentence)
            return sentence, i, sentences
    return None, -1, sentences

# def find_text_that_answers_question(context, answer):
#     for match in re.finditer(answer, context):
#         return match.start(), match.end()
#     return 0, len(context)-1

def split_sentences(body):
    return tokenizer.tokenize(body)

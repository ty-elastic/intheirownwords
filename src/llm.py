import os
import streamlit as st
import openai
import tiktoken
import time
import tiktoken

openai.api_type = "azure"
openai.api_key = os.environ['OPENAI_API_KEY']
openai.api_base = os.environ['OPENAI_BASE']
openai.api_version = os.environ['OPENAI_API_VERSION']

MAX_TOKENS=1024
MAX_CONTENT_TOKENS=4000
SAFETY_MARGIN=5

PROMPT_FAILED = "I'm unable to answer the question based on the results."

def truncate_text(text, max_tokens):
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text, len(tokens)
    return ' '.join(tokens[:max_tokens]), len(tokens)

def encoding_token_count(string: str, encoding_model: str) -> int:
    encoding = tiktoken.encoding_for_model(encoding_model)
    return len(encoding.encode(string))

# Generate a response from ChatGPT based on the given prompt
def query(prompt):
    
    # Truncate the prompt content to fit within the model's context length
    truncated_prompt, word_count = truncate_text(prompt, MAX_CONTENT_TOKENS - MAX_TOKENS - SAFETY_MARGIN)
    openai_token_count = encoding_token_count(prompt, os.environ['OPENAI_MODEL'])
    print(f"word_count = {word_count}, openai_token_count = {openai_token_count}")

    begin = time.perf_counter()
    response = openai.ChatCompletion.create(model=os.environ['OPENAI_MODEL'], deployment_id=os.environ['OPENAI_DEPLOYMENT_ID'],
                                            messages=[
                                                {"role": "system", "content": "You are a helpful assistant."},
                                                {"role": "user", "content": truncated_prompt}
                                                      ])
    end = time.perf_counter()
    time_taken = end - begin

    answer = response["choices"][0]["message"]["content"]
    answer_token_count = encoding_token_count(answer, os.environ['OPENAI_MODEL'])
    openai_token_count = response["usage"]["total_tokens"]
    cost = float((0.0015*(openai_token_count)/1000) + (0.002*(answer_token_count/1000)))

    return answer, time_taken, cost

def ask_question(context, question):
    prompt = f"Answer this question with a short answer: {question}\nUsing only the information from this Elastic Doc: {context}\nIf the answer is not contained in the supplied doc reply '{PROMPT_FAILED}' and nothing else"
    return query(prompt)
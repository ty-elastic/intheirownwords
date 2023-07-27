import streamlit as st
import es_clauses
import es_ml
import time
import llm
import os
import re

APP_NAME = "Informative Video Search Demo"

st.set_page_config(layout="wide", page_title=APP_NAME)

st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

def escape_markdown(text: str, version: int = 1, entity_type: str = None) -> str:
    """
    Helper function to escape telegram markup symbols.

    Args:
        text (:obj:`str`): The text.
        version (:obj:`int` | :obj:`str`): Use to specify the version of telegrams Markdown.
            Either ``1`` or ``2``. Defaults to ``1``.
        entity_type (:obj:`str`, optional): For the entity types ``PRE``, ``CODE`` and the link
            part of ``TEXT_LINKS``, only certain characters need to be escaped in ``MarkdownV2``.
            See the official API documentation for details. Only valid in combination with
            ``version=2``, will be ignored else.
    """
    if int(version) == 1:
        escape_chars = r'_*`['
    elif int(version) == 2:
        if entity_type in ['pre', 'code']:
            escape_chars = r'\`'
        elif entity_type == 'text_link':
            escape_chars = r'\)'
        else:
            escape_chars = r'_*[]()~`>#+-=|{}.!'
    else:
        raise ValueError('Markdown version must be either 1 or 2!')

    text = text.replace("$", "").strip()

    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

with st.form("clauses_query", clear_on_submit=False):
    origins = es_clauses.get_origins()
    origin = st.selectbox('Source', origins)
    query = st.text_input("Query: ")
    question_button = st.form_submit_button("Search")

if question_button:
    print(origin)
    st.cache_data.clear()
    results = es_clauses.find_clauses(origin, query)

    if results != None:
        print(results['text'])
        col1, col2, = st.columns(2)

        with col1:
            placeholder = st.empty()
            with placeholder:
                with st.spinner('loading...'):
                    time.sleep(0.1)
                placeholder.video(results['media_url'], format="video/mp4", start_time=int(results['start']))

        with col2:
            escaped = escape_markdown(results['text'])
            text = "### :green[_\"" + escaped + "\"_]" + "\r\n"
            st.markdown(text)
            if 'speaker.name' in results:
                title = "**" + results['speaker.name'] + "**, " + results['speaker.title'] + ", " + results['speaker.company']
                if 'speaker.email' in results:
                    text = "[" + title + "](mailto:" + results['speaker.email'] + ")"
                else:
                    text = "" + title
                st.markdown(text)
            text = results['date'].strftime('%Y-%m-%d')
            st.markdown(text)

            st.write("---")
            st.write("## ML Q&A using ELSER Results")
            answer = es_ml.ask_question(results['text'], query)
            st.write(f"**{answer}**")

            answer = es_ml.find_sentence_that_answers_question(results['text'], query, answer)
            escaped = escape_markdown(answer)
            text = "### :orange[_\"" + escaped + "\"_]" + "\r\n"
            st.markdown(text)

            if os.environ['OPENAI_API_KEY'] != None:
                st.write("---")
                st.write("## OpenAI Q&A using ELSER Results")

                answer, time_taken, cost = llm.ask_question(results['text'], query)
                if llm.PROMPT_FAILED in answer:
                    st.write("Insufficient data in Elasticsearch results")
                else:
                    st.write(f"**{answer.strip()}**")
                    st.write(f"\nCost: ${cost:0.6f}, ChatGPT response time: {time_taken:0.4f} sec")



        # with col3:
        #     if 'scene.frame_url' in results:
        #         st.image(results['scene.frame_url'])

        #st.write(results)    
    
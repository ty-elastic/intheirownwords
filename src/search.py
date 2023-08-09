import streamlit as st
import es_clauses
import es_ml
import time
import os
import re
import job
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import es_voices
import pandas as pd

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False

APP_NAME = "Informative Video Search Demo"

st.set_page_config(layout="wide", page_title=APP_NAME)

st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

METHOD_RRF_SUB="RRF Sub"
METHOD_RRF="RRF"
METHOD_HYBRID="Hybrid"

SEARCH_METHODS = [es_clauses.METHOD_HYBRID, es_clauses.METHOD_RRF]

def highlight_sentence(sentences, i):
    text = "### _\""
    for n, sentence in enumerate(sentences):
        escaped = escape_markdown(sentence)
        if n > 0:
            text = text + " "
        if i == n:
            text = text + ":orange[_" + escaped + "_]"
        else:
            text = text + escaped
    text = text + "\"_"
    return text

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

if os.path.isfile('auth/users.yaml'):
    with open('auth/users.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )

        name, authentication_status, username = authenticator.login('Login', 'main')
        if authentication_status is False:
            st.error('Username/password is incorrect')
        elif authentication_status is None:
            st.warning('Please enter your username and password')
else:
    st.session_state["authentication_status"] = True
    st.session_state["username"] = 'elastic'

if st.session_state["authentication_status"]:
    with st.sidebar:
        authenticator.logout('Logout', 'main')

    origins = es_clauses.get_origins()
    origin = st.selectbox('Source', origins)

    with st.form("clauses_query", clear_on_submit=False):
        query = st.text_input(":mag_right: **What do you want to know?**")

        speakers = es_voices.get_speakers(origin)
        speakers.insert(0, {'_id': 'anyone', 'speaker.name': 'anyone'})
        df = pd.DataFrame(speakers)
        #print(speakers)
        if len(df) > 0:
            options = df['_id'].tolist()
            values = df['speaker.name'].tolist()
            dic = dict(zip(options, values))
            speaker = st.selectbox(':microphone: Who said it?', options, format_func=lambda x: dic[x])
        else:
            speaker = st.selectbox(':microphone: Who said it?', ['anyone'])

        #method = st.selectbox('Search Method', SEARCH_METHODS)
        method=es_clauses.METHOD_HYBRID
        question_button = st.form_submit_button("Search")

        if question_button:
            print(speaker)
            st.cache_data.clear()
            if speaker == 'anyone':
                speaker = None
            results = es_clauses.find_clauses(origin, query, method, speaker_id=speaker)

            if results != None:
                text = "#### " + "[" + results['title'] + "](" + results["source_url"] + ")"
                st.markdown(text)
                text = results['date'].strftime('%Y-%m-%d')
                st.markdown(text)

                col1, col2, = st.columns(2)

                with col1:
                    answer = es_ml.ask_question(results['text'], query)
                    context_answer = None
                    if answer is not None:
                        context_answer, i, sentences = es_ml.find_sentence_that_answers_question(results['text'], query, answer)
                        if context_answer is not None:
                            text = highlight_sentence(sentences, i)
                            st.markdown(text)
                        else:
                            escaped = escape_markdown(results['text'])
                            text = ":orange[_\"" + escaped + "\"_]"
                            st.markdown(text)
                    
                    if 'speaker.name' in results:
                        title = "**" + results['speaker.name'] + "**, " + results['speaker.title'] + ", " + results['speaker.company']
                        if 'speaker.email' in results:
                            text = "[" + title + "](mailto:" + results['speaker.email'] + ")"
                        else:
                            text = "" + title
                        st.markdown(text)

                with col2:
                    placeholder = st.empty()
                    with placeholder:
                        with st.spinner('loading...'):
                            time.sleep(0.1)
                        placeholder.video(results['media_url'], format="video/mp4", start_time=int(results['start']))

                    # st.write("---")
                    # if 'scene.frame_url' in results:
                    #     st.image(results['scene.frame_url'])
                
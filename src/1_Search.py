import streamlit as st
import streamlit_authenticator as stauth
import es_clauses
import es_ml
import time
import os
import yaml
from yaml.loader import SafeLoader
import es_voices
import pandas as pd
import ui_helpers
import es_origins

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False

APP_NAME = "Informative Video Search Demo"
st.set_page_config(layout="wide", page_title=APP_NAME)

# hcol1, hcol2 = st.columns([0.2, 0.8], gap="medium")
# with hcol1:
#     header_logo = st.empty()
# with hcol2:
#     header_title = st.empty()

METHOD_RRF="RRF"
METHOD_HYBRID="Hybrid"

SEARCH_METHODS = [es_clauses.METHOD_HYBRID, es_clauses.METHOD_RRF]

if os.path.isfile('auth/users.yaml'):
    if "config" not in st.session_state:
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
    origin = st.selectbox('Collection', origins)
    origin_rec = es_origins.get_origin(origin)
    print(f"ORIGIN={origin}")

    hcol1, hcol2 = st.columns([0.2, 0.8], gap="medium")
    with hcol1:
        if origin_rec is not None:
            st.image(origin_rec['logo_url'], use_column_width=True)
        else:
            st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', use_column_width=True)
    with hcol2:
        if origin_rec is not None:
            st.title("Video Search")
        else:
            st.title(APP_NAME)

    with st.form("clauses_query", clear_on_submit=False):
        if origin is not None:

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

            kinds = es_clauses.get_kinds(origin)
            kinds.insert(0, 'any')
            print(kinds)
            kind = st.selectbox("Kind", kinds)


            #method = st.selectbox('Search Method', SEARCH_METHODS)
            method=es_clauses.METHOD_HYBRID
            question_button = st.form_submit_button("Search")

            if question_button:
                print(speaker)
                st.cache_data.clear()
                if speaker == 'anyone':
                    speaker = None
                if kind == 'any':
                    kind = None
                results = es_clauses.find_clauses(origin, query, method, speaker_id=speaker, kind=kind)

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
                                text = ui_helpers.highlight_sentence(sentences, i)
                                st.markdown(text)
                            else:
                                escaped = ui_helpers.escape_markdown(results['text'])
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
                    
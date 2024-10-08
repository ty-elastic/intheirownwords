import streamlit as st
import streamlit_authenticator as stauth
import es_clauses
import time
import os
import yaml
from yaml.loader import SafeLoader
import es_voices
import pandas as pd
import ui_helpers
import es_origins
from st_inject_api import CustomRule, init_global_tornado_hook, uninitialize_global_tornado_hook
from api_search_server import SearchHandler, StatusHandler, MediaHandler, OriginHandler, ImportHandler
import dateutil
import storage
from datetime import datetime
from dateutil.relativedelta import relativedelta

init_global_tornado_hook([CustomRule("/origins/.*", MediaHandler, name="/origins"),
                          CustomRule("/projects/.*", MediaHandler, name="/projects"),
                          CustomRule("/origin", OriginHandler, name="/origin"), 
                          CustomRule("/import", ImportHandler, name="/import"), 
                          CustomRule("/search", SearchHandler, name="/search"), 
                          CustomRule("/status", StatusHandler, name="/status")])

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False

APP_NAME = "Informative Video Search Demo"
st.set_page_config(layout="wide", page_title=APP_NAME)


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

            authenticator.login('main')
            if st.session_state["authentication_status"] is False:
                st.error('Username/password is incorrect')
            elif st.session_state["authentication_status"] is None:
                st.warning('Please enter your username and password')
else:
    st.session_state["authentication_status"] = True
    st.session_state["username"] = 'elastic'

if st.session_state["authentication_status"]:
    with st.sidebar:
        if os.path.isfile('auth/users.yaml'):
            authenticator.logout('Logout', 'main')

    origins = es_clauses.get_origins()
    origin = st.selectbox('Collection', origins)
    origin_rec = es_origins.get_origin(origin)
    print(f"ORIGIN={origin_rec}")

    hcol1, hcol2 = st.columns([0.15, 0.85], gap="small")
    with hcol1:
        if origin_rec is not None and 'logo_url' in origin_rec:
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
            #print(origin)
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

            by_date = st.checkbox(':date: When did they say it?', value=False, key="by_date")
            print(by_date)
            today = datetime.utcnow()
            last_year = today - relativedelta(years=1)
            date_range = st.date_input(
                "date",
                (last_year, today),
                max_value=today,
                format="YYYY-MM-DD",
                label_visibility="collapsed",
                #disabled=st.session_state.by_date==False
            )

            kinds = es_clauses.get_kinds(origin)
            kinds.insert(0, 'any')
            #print(kinds)
            kind = st.selectbox("Kind", kinds)

            question_button = st.form_submit_button("Search")
            if question_button:

                with st.spinner('Searching...'):
                    print(speaker)
                    st.cache_data.clear()
                    if speaker == 'anyone':
                        speaker = None
                    if kind == 'any':
                        kind = None
                    else:
                        kind = [kind]
                    size = None
                    if origin_rec != None:
                        size = origin_rec['results.size']
                    start = None
                    stop = None
                    if by_date:
                        start = date_range[0]
                        stop = date_range[1]
                    clauses = es_clauses.find_clauses(origin, query, speaker_id=speaker, kinds=kind, size=size, start=start, stop=stop)

                for clause in clauses:
                    text = "#### " + "[" + clause['title'] + "](" + clause["source_url"] + ")"
                    st.markdown(text)
                    date = dateutil.parser.isoparse(clause['date'])
                    text = date.strftime('%Y-%m-%d')
                    st.markdown(text)

                    col1, col2, = st.columns(2)

                    with col1:

                        text = ui_helpers.highlight_passage(clause['text'], clause['answer.start'], clause['answer.stop'])
                        st.markdown(text)

                        if 'speaker.name' in clause:
                            title = "**" + clause['speaker.name'] + "**, " + clause['speaker.title'] + ", " + clause['speaker.company']
                            if 'speaker.email' in clause:
                                text = "[" + title + "](mailto:" + clause['speaker.email'] + ")"
                            else:
                                text = "" + title
                            st.markdown(text)

                    with col2:
                        placeholder = st.empty()
                        with placeholder:
                            with st.spinner('loading...'):
                                time.sleep(0.1)
                            print(f"start={int(clause['media.start'])}")
                            if clause['media.url_http']:
                                placeholder.video(clause['media.url'], format="video/mp4", start_time=int(clause['media.start']))
                            else:
                                with storage.get_file(clause['media.url']) as video_file:
                                    placeholder.video(video_file.read(), format="video/mp4", start_time=int(clause['media.start']))

                    st.write("---")

                        # st.write("---")
                        # if 'scene.frame_url' in results:
                        #     st.image(results['scene.frame_url'])
                    
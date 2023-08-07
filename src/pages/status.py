import streamlit as st
from io import StringIO
import os
import job
import pandas as pd
import es_clauses

ORIGIN_ALL = "all"

APP_NAME = "Status"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True:
    st.error('not authenticated')
    st.stop()

def update_status(origin):
    data = {
        "origin": [],
        "title": [],
        "status": [],
        "started": [],
        "duration": []
    }
    jobs = job.get_status()
    for j in jobs:
        if origin is not ORIGIN_ALL and j["origin"] is not origin:
            continue
        data['origin'].append(j['origin'])
        data['title'].append(j['title'])
        data['status'].append(j['status'])
        data['started'].append(j['started'])
        data['duration'].append(str(j['duration']))

    df = pd.DataFrame(data)
    st.table(df)

with st.form("status_query", clear_on_submit=False):
    origins = es_clauses.get_origins()
    origins.insert(0, ORIGIN_ALL)
    origin = st.selectbox('Source', origins)
    question_button = st.form_submit_button("Search")

if question_button:
    update_status(origin)


import streamlit as st
from io import StringIO
import os
import job
import pandas as pd
import es_origins

ORIGIN_ALL = "all"

APP_NAME = "Import Status"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()

origins = es_origins.get_origins()
origins.insert(0, ORIGIN_ALL)
origin = st.selectbox('Collection', origins)

data = {
    "origin": [],
    "title": [],
    "status": [],
    "queued": [],
    "duration": []
}
jobs = job.get_status()
for j in jobs:
    if origin is ORIGIN_ALL or j["origin"] == origin:
        data['origin'].append(j['origin'])
        data['title'].append(j['title'])
        data['status'].append(j['status'])
        data['queued'].append(j['queued'])
        data['duration'].append(str(j['duration']))

df = pd.DataFrame(data)
st.table(df)

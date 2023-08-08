import streamlit as st
from io import StringIO
import os
import job
import pandas as pd
import es_clauses

ORIGIN_ALL = "all"

APP_NAME = "Videos"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()

def list_videos(origin):
    projects = es_clauses.get_projects(origin)
    df = pd.DataFrame(projects)

    st.dataframe(
        df,
        column_config={
            "media_url": st.column_config.LinkColumn("Media URL"),
            "source_url": st.column_config.LinkColumn("Source URL"),
        },
        hide_index=True,
    )

with st.form("video_query", clear_on_submit=False):
    origins = es_clauses.get_origins()
    origin = st.selectbox('Source', origins)
    question_button = st.form_submit_button("Search")

if question_button:
    list_videos(origin)

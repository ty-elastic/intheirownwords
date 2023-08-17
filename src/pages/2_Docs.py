import streamlit as st
from io import StringIO
import os
import job
from pytube import YouTube
import uuid
import es_origins
import es_clauses
import ui_helpers

APP_NAME = "Getting Started"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()

intro_markdown = ui_helpers.read_markdown_file("doc/ui.md")
st.markdown(intro_markdown, unsafe_allow_html=True)
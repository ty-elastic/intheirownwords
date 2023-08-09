import streamlit as st
from io import StringIO
import os
import job
from pytube import YouTube
import uuid
import es_clauses
import es_origins
import s3

APP_NAME = "Collections"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()


def validate_input(origin, homepage_url, uploaded_file):
    if uploaded_file is None:
        return False
    if homepage_url is None or homepage_url.strip() == "":
        return False
    if origin is None or origin.strip() == "":
        return False
    return True

#        fields = ["origin", "logo_url", "homepage_url"]

with st.form("upload", clear_on_submit=True):
    origin = st.text_input("Collection Name", help="e.g., company or organization name")
    homepage_url = st.text_input("Organization homepage URL", help='https://www.elastic.co/')
    uploaded_file = st.file_uploader("Logo", type=["svg","jpg","png"])
    upload_button = st.form_submit_button("Submit")

if upload_button:
    if validate_input(origin, homepage_url, uploaded_file):
        split_tup = os.path.splitext(uploaded_file.name)
        input = os.path.join(job.INGEST_DIR, str(uuid.uuid4()) + split_tup[1])
        with open(input, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logo_url = s3.upload_logo(input)
        es_origins.add_origin(origin, logo_url, homepage_url)
        os.remove(input)
    else:
        st.error('incomplete form')
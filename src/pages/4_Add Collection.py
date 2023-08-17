import streamlit as st
from io import StringIO
import os
import job
from pytube import YouTube
import uuid
import es_clauses
import es_origins
import s3
from streamlit_tags import st_tags, st_tags_sidebar
from hashlib import sha512

KINDS = ['Webinar', 'Tutorial', 'Meeting']


APP_NAME = "Collections"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()


def validate_input(origin, homepage_url):
    if homepage_url is None or homepage_url.strip() == "":
        return False
    if origin is None or origin.strip() == "":
        return False
    return True

#        fields = ["origin", "logo_url", "homepage_url"]

with st.form("upload", clear_on_submit=True):
    origin = st.text_input("Collection Name", help="e.g., company or organization name")
    homepage_url = st.text_input("Organization homepage URL", help='https://www.elastic.co/')
    media_kinds = keywords = st_tags(
        label='Media Kinds',
        text='Press enter to add more',
        value=KINDS,
        maxtags = 20)
    uploaded_file = st.file_uploader("Logo", type=["svg","jpg","png"])
    upload_button = st.form_submit_button("Submit")

if upload_button:
    if validate_input(origin, homepage_url):
        origin_id = str(sha512(origin.encode('utf-8')).hexdigest())
        logo_url = None
        if uploaded_file:
            logo_url = es_origins.upload_logo(uploaded_file, origin_id)
        es_origins.add_origin(origin_id, origin, logo_url, homepage_url, media_kinds)
    else:
        st.error('incomplete form')
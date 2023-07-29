import streamlit as st
from io import StringIO
import os
import q

APP_NAME = "Upload Video"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

with st.form("upload", clear_on_submit=False):
    source_url = st.text_input("source_url: ")
    title = st.text_input("title: ")
    date = st.text_input("date: ")
    kind = st.text_input("kind: ")
    origin = st.text_input("origin: ")
    enable_scenes = st.checkbox("enable_scenes", value=True)
    uploaded_file = st.file_uploader("Choose a file")
    upload_button = st.form_submit_button("Upload")

if upload_button:

    input = os.path.join("ingest",uploaded_file.name)
    with open(input, "wb") as f: 
      f.write(uploaded_file.getbuffer())         

    q.enqueue(input, source_url, title, date, kind, origin, enable_scenes)

import streamlit as st
from io import StringIO
import os
import job

APP_NAME = "Upload Video"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

with st.form("upload", clear_on_submit=True):
    source_url = st.text_input("URL of page video was scrapped from (for reference): ")
    title = st.text_input("title: ")
    date = st.date_input("date recorded: ")
    kind = st.text_input("kind: (e.g., webinar, tutorial)")
    origin = st.text_input("origin: (company)")
    enable_slides = st.checkbox("content contains slides", value=True)
    uploaded_file = st.file_uploader("Choose a file")
    upload_button = st.form_submit_button("Upload")

if upload_button:

    input = os.path.join("ingest",uploaded_file.name)
    with open(input, "wb") as f: 
      f.write(uploaded_file.getbuffer())         

    job.enqueue(input, source_url, title, date, kind, origin, enable_slides)

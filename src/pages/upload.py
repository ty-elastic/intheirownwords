import streamlit as st
from io import StringIO
import os
import job

APP_NAME = "Upload Video"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True:
    st.stop()

with st.form("upload", clear_on_submit=True):
    source_url = st.text_input(
        "URL of page video was scrapped from (for reference)")
    title = st.text_input("Title")
    date = st.date_input("Date Recorded")
    kind = st.text_input("Media Kind", help="e.g., webinar, tutorial")
    origin = st.text_input("Media Source", help="company name")
    enable_slides = st.checkbox("Slide Content?", value=True, help="uncheck if content does not contain slides")
    uploaded_file = st.file_uploader("Media File", type="mp4", help="use ffmpeg to coerce media into h264+aac/mp4")
    upload_button = st.form_submit_button("Upload")

if upload_button:
    input = os.path.join(job.INGEST_DIR, uploaded_file.name)
    with open(input, "wb") as f:
        f.write(uploaded_file.getbuffer())

    job.enqueue(input, source_url, title, date,
                kind, origin, enable_slides)

import streamlit as st
from io import StringIO
import os
import job
from pytube import YouTube
import uuid
import es_clauses

APP_NAME = "Upload Video"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()


def validate_input(source_url, title, kind, origin, youtube_link, uploaded_file):
    if source_url is None or source_url.strip() == "":
        return False
    if title is None or title.strip() == "":
        return False
    if kind is None or kind.strip() == "":
        return False
    if origin is None or origin.strip() == "":
        return False
    if (youtube_link is None or youtube_link.strip() == "") and (uploaded_file is None):
        return False
    return True


with st.form("upload", clear_on_submit=True):
    source_url = st.text_input(
        "URL of page video was scrapped from (for reference)")
    title = st.text_input("Title")
    date = st.date_input("Date Recorded")
    kind = st.text_input("Media Kind", help="e.g., webinar, tutorial")
    origin = st.text_input("Collection", help="e.g., company or organization name")
    enable_slides = st.checkbox("Slide Content?", value=True, help="uncheck if content does not contain slides")
    youtube_link = st.text_input("URL to YouTube Video", help='https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    youtube_button = st.form_submit_button("Ingest from YouTube")
    uploaded_file = st.file_uploader("Media File", type="mp4", help="use ffmpeg to coerce media into h264+aac/mp4")
    upload_button = st.form_submit_button("Ingest from File")

if youtube_button:
    if validate_input(source_url, title, kind, origin, youtube_link, uploaded_file):
        print(youtube_link)
        yt = YouTube(youtube_link)
        videos = yt.streams.filter(progressive=True, file_extension='mp4').desc()

        print(videos)

        input = videos.first().download(output_path=job.INGEST_DIR,skip_existing=False,filename=str(uuid.uuid4()) + ".mp4")
        print(input)
        job.enqueue(input, source_url, title, date,
                    kind, origin, enable_slides)
    else:
        st.error('incomplete form')

if upload_button:
    if validate_input(source_url, title, kind, origin, youtube_link, uploaded_file):
        input = os.path.join(job.INGEST_DIR, str(uuid.uuid4()) + ".mp4")

        with open(input, "wb") as f:
            f.write(uploaded_file.getbuffer())

        job.enqueue(input, source_url, title, date,
                    kind, origin, enable_slides)
    else:
        st.error('incomplete form')
import streamlit as st
import os
import api_import_client
import uuid
import es_origins
import storage

APP_NAME = "Import Video"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()

origins = es_origins.get_origins()
origin = st.selectbox('Collection', origins)
origin_record = es_origins.get_origin(origin)

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
    #origin = st.text_input("Collection", help="e.g., company or organization name")
    #origin = st.selectbox('Collection', es_origins.get_origins())
    kinds = []
    if origin_record is not None:
        kinds = origin_record['kinds']
        print(kinds)
    kind = st.selectbox("Media Kind", kinds)
    save_frames = st.checkbox("Save Slide Content?", value=False, help="check to save frames with possible slide content as images")
    youtube_link = st.text_input("URL to YouTube Video", help='https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    youtube_button = st.form_submit_button("Ingest from YouTube")
    uploaded_file = st.file_uploader("Media File", type="mp4", help="use ffmpeg to coerce media into h264+aac/mp4")
    upload_button = st.form_submit_button("Ingest from File")

if youtube_button:
    if validate_input(source_url, title, kind, origin, youtube_link, uploaded_file):
        api_import_client.enqueue(source_url, title, date,
                    kind, origin, save_frames, youtube_url=youtube_link)
    else:
        st.error('incomplete form')

if upload_button:
    if validate_input(source_url, title, kind, origin, youtube_link, uploaded_file):
        input = os.path.join(storage.INGEST_DIR, str(uuid.uuid4()) + ".mp4")

        with open(input, "wb") as f:
            f.write(uploaded_file.getbuffer())

        api_import_client.enqueue(source_url, title, date,
                    kind, origin, save_frames, local_path=input)
    else:
        st.error('incomplete form')
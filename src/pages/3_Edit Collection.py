import streamlit as st
import es_voices
import es_origins

APP_NAME = "Edit Collection"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()

forms = {}

origins = es_origins.get_origins()
origin_selection = st.selectbox('Collection', origins)
print(origin_selection)
origin_record = es_origins.get_origin(origin_selection)
print(origin_record)

with st.form('edit', clear_on_submit=True):
    origin = st.text_input("Collection Name", value=origin_record['origin'], help="e.g., company or organization name")
    homepage_url = st.text_input("Organization homepage URL", value=origin_record['homepage_url'], help='https://www.elastic.co/')
    uploaded_file = st.file_uploader("Logo", type=["svg","jpg","png"])
    upload_button = st.form_submit_button("Submit")

if upload_button:
    print("updating " + origin)
    # es_voices.update_speaker(origin['_id'], forms[voice['_id']]['speaker_name'],
    #                         forms[voice['_id']]['speaker_title'], forms[voice['_id']
    #                                                                     ]['speaker_company'],
    #                         forms[voice['_id']]['speaker_email'])
    # forms[voice['_id']]['placeholder'].empty()
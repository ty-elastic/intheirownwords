import streamlit as st
import es_voices
import es_clauses

APP_NAME = "Update Voices"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()

forms = {}

origins = es_clauses.get_origins()
origin = st.selectbox('Source', origins)

voices = es_voices.get_unassigned_voices(origin)

for voice in voices:
    forms[voice['_id']] = {}
    placeholder = st.empty()
    forms[voice['_id']]['placeholder'] = placeholder
    with placeholder.container():
        if 'example.source_url' in voice:
            st.write(voice['example.source_url'])
        st.write(str(voice['example.start']) +
                    " - " + str(voice['example.end']))
        st.video(voice['example.url'], format="video/mp4",
                    start_time=int(voice['example.start']))
        with st.form(voice['_id'], clear_on_submit=True):
            forms[voice['_id']]['speaker_name'] = st.text_input(
                "Name: ")
            forms[voice['_id']]['speaker_title'] = st.text_input(
                "Title: ")
            forms[voice['_id']]['speaker_company'] = st.text_input(
                "Company: ")
            forms[voice['_id']]['speaker_email'] = st.text_input(
                "Email: ")
            forms[voice['_id']]['update'] = st.form_submit_button(
                "Update")
        st.write("---")

        if forms[voice['_id']]['update']:
            print("updating " + voice['_id'])
            es_voices.update_speaker(voice['_id'], forms[voice['_id']]['speaker_name'],
                                    forms[voice['_id']]['speaker_title'], forms[voice['_id']
                                                                                ]['speaker_company'],
                                    forms[voice['_id']]['speaker_email'])
            forms[voice['_id']]['placeholder'].empty()
import streamlit as st
import es_voices

APP_NAME = "Update Voices"

st.set_page_config(layout="wide", page_title=APP_NAME)

st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

voices = es_voices.get_unassigned_voices()
forms = {}
for voice in voices:
    forms[voice['_id']] = {}
    with st.form(voice['_id'], clear_on_submit=False):
        if 'example.source_url' in voice:
            st.write(voice['example.source_url'])
        st.write(str(voice['example.start']) + " - " +  str(voice['example.end']))
        st.video(voice['example.url'], format="video/mp4", start_time=int(voice['example.start']))
        forms[voice['_id']]['speaker_name'] = st.text_input("Name: ")
        forms[voice['_id']]['speaker_title']  = st.text_input("Title: ")
        forms[voice['_id']]['speaker_company']  = st.text_input("Company: ")
        forms[voice['_id']]['speaker_email']  = st.text_input("Email: ")
        forms[voice['_id']]['update'] = st.form_submit_button("Update")
        if forms[voice['_id']]['update']:
            es_voices.update_speaker(voice['_id'], forms[voice['_id']]['speaker_name'], 
                                     forms[voice['_id']]['speaker_title'], forms[voice['_id']]['speaker_company'],
                                     forms[voice['_id']]['speaker_email'])
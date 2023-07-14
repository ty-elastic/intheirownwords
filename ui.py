import streamlit as st
import es_clauses
import batteries
import time

APP_NAME = "Informative Video Search Demo"

st.set_page_config(layout="wide", page_title=APP_NAME)

st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt5d10f3a91df97d15/620a9ac8849cd422f315b83d/logo-elastic-vertical-reverse.svg', width=100)
st.title(APP_NAME)

with st.form("clauses_query", clear_on_submit=False):
    origins = es_clauses.get_origins()
    origin = st.selectbox('Source', origins)
    query = st.text_input("Query: ")
    question_button = st.form_submit_button("Search")

if question_button:
    print(origin)
    st.cache_data.clear()
    results = es_clauses.find_clauses(origin, query)
    print(results['text'])
    if results != None:

        col1, col2, col3 = st.columns(3)

        with col1:
            placeholder = st.empty()
            with placeholder:
                with st.spinner('loading...'):
                    time.sleep(0.1)
                placeholder.video(results['media_url'], format="video/mp4", start_time=int(results['start']))

        with col2:
            escaped = batteries.escape_markdown(results['text'])
            text = "### :green[_\"" + escaped + "\"_]" + "\r\n"
            st.markdown(text)
            if 'speaker.name' in results:
                title = "**" + results['speaker.name'] + "**, " + results['speaker.title'] + ", " + results['speaker.company']
                if 'speaker.email' in results:
                    text = "[" + title + "](mailto:" + results['speaker.email'] + ")"
                else:
                    text = "" + title
                st.markdown(text)
            text = results['date'].strftime('%Y-%m-%d')
            st.markdown(text)

        with col3:
            if 'scene.frame_url' in results:
                st.image(results['scene.frame_url'])

        #st.write(results)    
    
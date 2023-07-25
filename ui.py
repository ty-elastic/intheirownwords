import streamlit as st
import es_clauses
import batteries
import time

APP_NAME = "Informative Video Search Demo"

st.set_page_config(layout="wide", page_title=APP_NAME)

st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
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

    if results != None:
        print(results['text'])
        col1, col2, = st.columns(2)

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

            st.write("---")
            st.write("## ML Q&A using ELSER Results")
            answer = es_clauses.ask_question(results['text'], query)
            st.write(f"**{answer}**")

            answer = es_clauses.find_sentence_that_answers_question(results['text'], query, answer)
            escaped = batteries.escape_markdown(answer)
            text = "### :orange[_\"" + escaped + "\"_]" + "\r\n"
            st.markdown(text)

        # with col3:
        #     if 'scene.frame_url' in results:
        #         st.image(results['scene.frame_url'])

        #st.write(results)    
    
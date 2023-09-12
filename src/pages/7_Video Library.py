import streamlit as st
import pandas as pd
import es_clauses
import delete

ORIGIN_ALL = "all"

APP_NAME = "Video Library"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()

origins = es_clauses.get_origins()
origin = st.selectbox('Collection', origins)
#origin_record = es_origins.get_origin(origin)


projects = es_clauses.get_projects(origin)
df = pd.DataFrame(projects)
delete_checks = []
for project in projects:
    delete_checks.append(False)

if len(projects) > 0:
    df.insert(0, 'delete', delete_checks)
    df = df.drop(columns=['kind', 'date', 'origin'])


st.warning("Please reload after delete; table does not update automatically", icon="⚠️")

with st.form(key="lib", clear_on_submit=True):

    edited_df = st.data_editor(
        df,
        column_config={
            "media.url": st.column_config.LinkColumn("Media URL"),
            "source_url": st.column_config.LinkColumn("Source URL"),
            "delete": "Delete ?",
        },
        disabled=["project_id", "media.url", "date_uploaded", "title", "source_url"],
        hide_index=True, 
        key="projects"
    )

    delete_btn = st.form_submit_button("Delete")
    if delete_btn:
        for index, row in edited_df.iterrows():
            #print(row)
            if row['delete']:
                print(f"about to delete={row['project_id']}")
                delete.delete_project(row['project_id'])
                #df=df.drop(df.index[index])
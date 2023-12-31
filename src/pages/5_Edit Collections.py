import streamlit as st
import es_clauses
import es_origins
from streamlit_tags import st_tags, st_tags_sidebar
from hashlib import sha512
import os
import storage
import delete

KINDS = ['Webinar', 'Tutorial', 'Meeting']

APP_NAME = "Edit Collections"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

if 'authentication_status' not in st.session_state:
    st.session_state['authentication_status'] = False
if st.session_state["authentication_status"] != True or st.session_state["username"] != 'elastic':
    st.error('not authenticated')
    st.stop()

def validate_input(origin, homepage_url):
    if homepage_url is None or homepage_url.strip() == "":
        return False
    if origin is None or origin.strip() == "":
        return False
    return True

create_new = st.checkbox('Create New Collection', key="create_new", value=True)

origins = es_origins.get_origins()
legacy_origins = es_clauses.get_origins()
origins_clean = (origins + list(set(legacy_origins) - set(origins)))
origin_selection = st.selectbox('Existing Collection', origins_clean, disabled=st.session_state.create_new)
if origin_selection is None:
    origin_selection = ''
print(origin_selection)
origin_record = es_origins.get_origin(origin_selection)



if create_new:
    origin_record = None
    origin_selection = ''
if origin_record is None:
    origin_record = {'origin':origin_selection, 'homepage_url':'', 'kinds':KINDS, 'results.size':1}
print(origin_record)

origin=origin_record['origin']

with st.form('edit', clear_on_submit=True):
    
    origin = st.text_input("Collection Name", value=origin_record['origin'], help="e.g., company or organization name", disabled=st.session_state.create_new == False)
    homepage_url = st.text_input("Organization homepage URL", value=origin_record['homepage_url'], help='https://www.elastic.co/')
    media_kinds = st_tags(
        label='Media Kinds',
        text='Press enter to add more',
        value=origin_record['kinds'],
        maxtags = 20)
    results_size = st.number_input("search result size", min_value=1,max_value=10,value=origin_record['results.size'],format="%d")
    
    hcol1, hcol2 = st.columns([0.1, 0.9], gap="small")
    with hcol1:
        if 'logo_url' in origin_record:
            st.image(origin_record['logo_url'], use_column_width=True)
    with hcol2:
        uploaded_file = st.file_uploader("Logo", type=["svg","jpg","png"])

    upload_button = st.form_submit_button("Submit")
    delete_button = False
    if not create_new:
        delete_button = st.form_submit_button("Delete")

if delete_button:
    delete.delete_origin(origin)

if upload_button:
    if validate_input(origin, homepage_url):    
        origin_id = es_origins.hash_origin_id(origin)
        print(f"kinds={media_kinds}")
        if media_kinds == None:
            media_kinds = []
        
        logo_url = None
        if uploaded_file:
            logo_url = storage.upload_logo(uploaded_file.name, uploaded_file.getbuffer(), origin_id)

        if create_new or origin not in origins:
            print("adding " + origin)
            es_origins.add_origin(origin_id, origin, logo_url, homepage_url, media_kinds, results_size)
        else:
            print("updating " + origin)
            es_origins.update_origin(origin_id, origin, logo_url, homepage_url, media_kinds, results_size)
    else:
        st.error('incomplete form')

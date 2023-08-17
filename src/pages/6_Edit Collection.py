import streamlit as st
import es_voices
import es_origins
from streamlit_tags import st_tags, st_tags_sidebar

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

if origin_record:
    with st.form('edit', clear_on_submit=False):
        origin = st.text_input("Collection Name", value=origin_record['origin'], help="e.g., company or organization name")
        homepage_url = st.text_input("Organization homepage URL", value=origin_record['homepage_url'], help='https://www.elastic.co/')
        media_kinds = keywords = st_tags(
            label='Media Kinds',
            text='Press enter to add more',
            value=origin_record['kinds'],
            maxtags = 20)
        
        hcol1, hcol2 = st.columns([0.1, 0.9], gap="small")
        with hcol1:
            if 'logo_url' in origin_record:
                header_logo = st.image(origin_record['logo_url'], use_column_width=True)
        with hcol2:
            uploaded_file = st.file_uploader("Replace Logo", type=["svg","jpg","png"])


        upload_button = st.form_submit_button("Submit")

    if upload_button:
        print("updating " + origin)
        logo_url = origin_record['logo_url']
        if uploaded_file:
            logo_url = es_origins.upload_logo(uploaded_file, origin_record['_id'])
        es_origins.update_origin(origin_record['_id'], origin, logo_url, homepage_url, media_kinds)
       # origin_record = es_origins.get_origin(origin)
        #origins = es_origins.get_origins()
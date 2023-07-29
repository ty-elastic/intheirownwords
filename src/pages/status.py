import streamlit as st
from io import StringIO
import os
import job
import pandas as pd

APP_NAME = "Status"
st.set_page_config(layout="wide", page_title=APP_NAME)
st.image('https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt601c406b0b5af740/620577381692951393fdf8d6/elastic-logo-cluster.svg', width=100)
st.title(APP_NAME)

def update_status():
  data = {
    "title": [],
    "status": []
  }
  jobs = job.get_status()
  for j in jobs:
      data['title'].append(j['title'])
      data['status'].append(j['status'])

  df = pd.DataFrame(data)
  st.table(df)

update_status()

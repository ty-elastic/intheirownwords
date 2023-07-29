#!/bin/bash

set -o allexport
source env.vars
set +o allexport

source /opt/conda/etc/profile.d/conda.sh
conda activate intheirownwords
streamlit run src/ui_search.py
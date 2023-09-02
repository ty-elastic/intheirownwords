#!/bin/bash

set -o allexport
source env.vars
set +o allexport

source /opt/conda/etc/profile.d/conda.sh
conda activate intheirownwords
python src/main.py
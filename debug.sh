#!/bin/bash

set -o allexport
source env.vars
set +o allexport

conda activate intheirownwords
python src/main.py $@
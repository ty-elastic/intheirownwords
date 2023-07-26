#!/bin/bash

set -o allexport
source env.vars
set +o allexport

conda run -n intheirownwords python src/main.py $@


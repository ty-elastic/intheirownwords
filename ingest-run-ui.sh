docker run --rm --runtime=nvidia --gpus all --env-file env.vars -p 8501:8501 -v $PWD/prj:/home/ubuntu/intheirownwords/prj -v $PWD/ingest:/home/ubuntu/intheirownwords/ingest -v /usr/local/cuda:/usr/local/cuda --entrypoint "" intheirownwords-ingest conda run --no-capture-output -n intheirownwords streamlit run ui_search.py
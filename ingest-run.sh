docker run --rm --runtime=nvidia --gpus all --env-file env.vars -v $PWD/prj:/home/ubuntu/intheirownwords/prj -v $PWD/ingest:/home/ubuntu/intheirownwords/ingest -v /usr/local/cuda:/usr/local/cuda intheirownwords-ingest $@
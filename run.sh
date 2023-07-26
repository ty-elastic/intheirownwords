docker build -t ty-elastic/intheirownwords

docker run --rm --runtime=nvidia --gpus all --env-file env.vars -v $PWD/prj:/prj -v $PWD/ingest:/ingest -v /usr/local/cuda:/usr/local/cuda ty-elastic/intheirownwords $@
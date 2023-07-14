conda activate intheirownwords
source ./vars.sh

sudo docker run --rm --runtime=nvidia --gpus all --env-file vars.env -v $PWD/prj:/prj -v /usr/local/cuda:/usr/local/cu
da -v $PWD/../ingest:/ingest 48ff35cd9e8e2b488b4c1538965071f078c1ab1352cc0a2152ec909971626d52 /ingest/digikey-dip.mp4 04/19/23 "DIP Switches 101" tutorial digikey
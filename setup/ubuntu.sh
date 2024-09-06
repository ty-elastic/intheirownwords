#!/bin/bash

mkdir -p ../prj
mkdir -p ../ingest

gpu="false"
develop="false"
uionly="false"
while getopts d:u:g: flag
do
    case "${flag}" in
        d) develop="true";;
        u) uionly="true";;
        g) gpu="true";;
    esac
done
echo "develop=$develop"
echo "uionly=$uionly"
echo "gpu=$gpu"

# install build essentials
echo "installing build tooling..."
sudo apt update
sudo apt install -y build-essential

if [ "$gpu" == "true" ]; then
  if [[ $(which nvidia-smi) ]]; then
    echo "nvidia driver is installed."
  else
    # install nvidia driver and CUDA toolkit
    echo "install nvidia driver and CUDA toolkit (this can take some time)..."
    wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
    sudo sh cuda_11.8.0_520.61.05_linux.run --silent --driver --toolkit
    nvidia-smi
  fi
fi

# install docker
if [[ $(which docker) && $(docker --version) ]]; then
  echo "docker is installed."
else
  echo "installing docker..."
  sudo apt-get update \
    && sudo apt-get install ca-certificates curl gnupg

  sudo install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update \
    && sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  sudo systemctl --now enable docker
  sudo usermod -aG docker $USER
fi

if [ "$uionly" == "false" ]; then
  # install nvidia/cuda docker extensions
  echo "installing nvidia docker extensions..."
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
        && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
              sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
              sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
  sudo docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi

  # build container
  echo "building ingest container..."
  sudo docker build -t intheirownwords-ingest -f ../Dockerfile.ingest ../
fi

# build container
echo "building ui container..."
sudo docker build -t intheirownwords-ui -f ../Dockerfile.ui ../

if [ "$develop" == "true" ]; then

  sudo apt install -y ffmpeg

  sudo add-apt-repository -y ppa:alex-p/tesseract-ocr5
  sudo apt update
  sudo apt install -y tesseract-ocr
  sudo wget -O /usr/share/tesseract-ocr/5/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata

  # install conda
  echo "installing conda..."
  CONDA_DIR=/opt/conda
  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
  chmod a+x ./miniconda.sh
  sudo ./miniconda.sh -b -p $CONDA_DIR
  export PATH=$CONDA_DIR/bin:$PATH

  # setup conda
  echo "setup conda env"
  conda create -y --name intheirownwords python=3.10
  source /opt/conda/etc/profile.d/conda.sh
  conda activate intheirownwords

  echo "installing dependencies..."
  if [ "$uionly" == "false" ]; then
    conda env config vars set CUDA_HOME="/usr/local/cuda"
    conda activate intheirownwords

    # base dependencies for pytorch
    conda install -y pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.8 -c pytorch -c nvidia
    # install required python libs
    pip install git+https://github.com/pyannote/pyannote-audio.git@develop
    pip install -r ingest-requirements.txt
  fi

  pip install -r ui-requirements.txt
fi
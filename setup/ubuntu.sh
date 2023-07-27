#!/bin/bash

develop="false"
uionly="false"
while getopts d:u: flag
do
    case "${flag}" in
        d) develop="true";;
        u) uionly="true";;
    esac
done
echo "develop=$develop"
echo "uionly=$uionly"

# install build essentials
echo "installing build tooling..."
sudo apt update 
sudo apt install -y build-essential

if [ "$uionly" == "false" ]; then
  if [[ $(which nvidia-smi) ]]; then
    echo "nvidia driver is installed."
  else
    # install nvidia driver and CUDA toolkit
    echo "install nvidia driver and CUDA toolkit (this can take some time)..."
    wget https://developer.download.nvidia.com/compute/cuda/11.7.1/local_installers/cuda_11.7.1_515.65.01_linux.run
    sudo sh cuda_11.7.1_515.65.01_linux.run --silent --driver --toolkit
    nvidia-smi
  fi
fi

# install docker
if [[ $(which docker) && $(docker --version) ]]; then
  echo "docker is installed."
else
  echo "installing docker..."
  curl https://get.docker.com | sh \
    && sudo systemctl --now enable docker

  sudo usermod -aG docker $USER
  newgrp docker
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
  sudo docker run --rm --runtime=nvidia --gpus all nvidia/cuda:11.6.2-base-ubuntu20.04 nvidia-smi

  # build container
  echo "building ingest container..."
  docker build -t intheirownwords-ingest -f ../Dockerfile.ingest ../
fi

# build container
echo "building ui container..."
docker build -t intheirownwords-ui -f ../Dockerfile.ui ../

if [ "$develop" == "true" ]; then
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
    conda install -y pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia
    # install tesseract binaries
    conda install -y  -c conda-forge tesseract
    # install required python libs
    pip install git+https://github.com/pyannote/pyannote-audio.git@develop
    pip install -r ingest-requirements.txt
  fi

  pip install -r ui-requirements.txt
fi
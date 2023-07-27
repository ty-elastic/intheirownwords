#!/bin/bash

# install conda
echo "installing conda..."

CONDA_DIR=/opt/conda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
chmod a+x ./miniconda.sh
sudo ./miniconda.sh -b -p $CONDA_DIR
export PATH=$CONDA_DIR/bin:$PATH

# setup conda
conda create -y --name intheirownwords python=3.10
conda init bash
source ~/.bashrc

conda activate intheirownwords
conda env config vars set CUDA_HOME="/usr/local/cuda"
conda activate intheirownwords

# base dependencies for pytorch
echo "installing dependencies..."

conda install -y pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia

# install tesseract binaries
conda install -y  -c conda-forge tesseract

# install required python libs
pip install git+https://github.com/pyannote/pyannote-audio.git@develop
pip install -r requirements.txt
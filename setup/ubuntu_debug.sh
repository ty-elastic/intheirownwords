#!/bin/bash

# install conda
CONDA_DIR=/opt/conda
wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
./miniconda.sh -b -p /opt/conda

# setup conda
conda create --name intheirownwords python=3.10
conda env config vars set CUDA_HOME="/usr/local/cuda"

conda init bashrc
conda activate intheirownwords

# base dependencies for pytorch
conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia

# install tesseract binaries
conda install -c conda-forge tesseract

# install required python libs
pip install git+https://github.com/pyannote/pyannote-audio.git@develop
pip install -r requirements.txt
#!/bin/bash

# install build essentials
echo "installing build tooling..."
sudo apt update 
sudo apt install -y build-essential

# install nvidia driver and CUDA toolkit
echo "install nvidia driver and CUDA toolkit (this can take some time)..."
wget https://developer.download.nvidia.com/compute/cuda/11.7.1/local_installers/cuda_11.7.1_515.65.01_linux.run
sudo sh cuda_11.7.1_515.65.01_linux.run --silent --driver --toolkit

nvidia-smi

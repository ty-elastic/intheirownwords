#!/bin/bash

# install build essentials
sudo apt update 
sudo apt install build-essential

# install nvidia drivers
# wget https://us.download.nvidia.com/tesla/470.199.02/NVIDIA-Linux-x86_64-515.65.01.run
# chmod a+x NVIDIA-Linux-x86_64-515.65.01.run
# sudo ./NVIDIA-Linux-x86_64-515.65.01.run

# install nvidia cuda toolkit
wget https://developer.download.nvidia.com/compute/cuda/11.7.1/local_installers/cuda_11.7.1_515.65.01_linux.run
sudo sh cuda_11.7.1_515.65.01_linux.run
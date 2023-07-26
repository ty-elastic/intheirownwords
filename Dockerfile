FROM ubuntu:latest


# https://pythonspeed.com/articles/activate-conda-dockerfile/

WORKDIR /home

# Install base utilities
RUN apt-get update \
    && apt-get install -y build-essential \
    && apt-get install -y wget \
    && apt-get install -y git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y ffmpeg
#     && apt-get install -y libsm6 \
#     && apt-get install -y libxext6

# Install miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH

RUN conda create --name intheirownwords python=3.10 && \
    conda env config vars set CUDA_HOME="/usr/local/cuda"

SHELL ["conda", "run", "-n", "intheirownwords", "/bin/bash", "-c"]

RUN conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia

# install tesseract binaries
RUN conda install -c conda-forge tesseract

# install required python libs
RUN pip install git+https://github.com/pyannote/pyannote-audio.git@develop
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py .

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "intheirownwords", "python", "main.py"]
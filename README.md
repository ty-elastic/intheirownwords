# In Their Own Words

An exemplary project to demonstrate the art-of-the-possible for search of informative video using off-the-shelf ML models and Elasticsearch!

## Background

Modern organizations, from large enterprises to school districts, share a lot of pertinent and timely information through video content (e.g., Town Halls, Webinars, Board Meetings). Typically such content addresses a wide range of topics within a given video, with each topic of interest only to a specific subset of the audience. Without a good intra-video search option, viewers are forced to consume such content linearly. At best, this potentially wastes a viewer's valuable time; at worst, it creates enough of a barrier to consumption that pertinent information (which could be a catalyst to further productivity) goes unwatched.

In general, few options exist to make informative, often private (e.g., internal use only), video practically searchable. Some existing projects summarize video content using a public Speech-To-Text (STT) engine and LLM (e.g., as offered by OpenAI), and then offer search on top of the summarized output. Use of such services, however, potentially puts private information at risk for public exposure. Further, and arguably more importantly, speakers in informative video are generally:
* subject matter experts
* well-spoken
* already producing expertly-curated summarized content

Adding a LLM to summarize their carefully chosen words can easily skew their intended meaning. As an example, consider a company townhall meeting which includes a discussion from the VP of HR regarding a layoff: the words spoken have been carefully selected and their nuance matters. This project (as the name implies) intentionally forgoes such paraphrasing and instead lets subject matter experts speak for themselves.

## Novelty

### Topic Separation

One challenge of transcribing spoken content is determining topic boundaries: in essence, how do you know if a given sentence belongs to a new or previous topic? This concept is exasperated by the nature of human speech: we often inject unrelated filler in-between 2 or more related sentences of substance.

To address this, we employ a sentence similarity embedding over a sliding sentence window of configurable length to try to separate text into topics or clauses. If the widow is 'book-ended' by similar sentences, we accept the (potentially) filler sentences sandwiched in-between as being part of the clause. We augment this topic detection by further using changes in speaker and/or scene (typically slides). Together, this is proving to be a reasonably effective approach to topic separation.

### Search Accuracy

Keyword search of STT transcriptions (e.g., search over sentences in a caption track) is typically not an effective way to make video searchable. We address this issue two-fold:
1. After grouping sentences by topic, we generate symantec encodings of clauses (related sentences) using the [Elastic Learned Sparse EncodeR (ELSER)](https://www.elastic.co/guide/en/machine-learning/current/ml-nlp-elser.html) model. ELSER-based symantec search of the clauses is a remarkably effective means of searching by question.
2. We use [Elastic hybrid search](https://www.elastic.co/guide/en/elasticsearch/reference/8.7/knn-search.html#_combine_approximate_knn_with_other_features) to combine the ELSER results with BM25 search over keywords in the OCR'd slide content.

# Architecture

![Architecture](doc/arch.jpg?raw=true "Architecture")

# Tenets

* Don’t trust a LLM to summarize critical information; let people speak for themselves
* Don’t share private data with a hosted AI service

# Getting Started

## Hugging Face Models

Some of the models require a [Hugging Face](https://huggingface.co) token and acceptance of respective user agreements. 

1. [Create a Hugging Face account](https://huggingface.co/join)
2. [Generate a token](https://huggingface.co/settings/tokens)
3. Accept the user agreement for the following models: [Segmentation](https://huggingface.co/pyannote/segmentation), [Voice Activity Detection (VAD)](https://huggingface.co/pyannote/voice-activity-detection), and [Speaker Diarization](https://huggingface.co/pyannote/speaker-diarization).

## Elastic Instance

You will need a modern Elastic instance with sufficient ML resources (at least 4GB of RAM) to support this demo. You can start a 2 week free trial of Elastic Cloud [here](https://cloud.elastic.co/registration). Be sure to select "4 GB RAM" for the Machine Learning instance type. When you create the instance, you will be provided a password for the `elastic` user; make note of it. Additionally, from the Deployments page, you will need the endpoint of your Elasticsearch instance.

### Create Indices and Pipelines

```
DELETE /clauses
PUT /clauses
{
 "mappings": {
   "properties": {
     "project_id": {
       "type": "keyword"
     }, 
     "media_url": {
       "type": "keyword"
     },
     "title": {
       "type": "text"
     },
     "date": {
       "type": "date"
     },
     "kind": {
       "type": "keyword"
     },
     "origin": {
       "type": "keyword"
     },
     
     "scene.start": {
       "type": "float"
     },
     "scene.end": {
       "type": "float"
     },
     "scene.frame_text": {
       "type": "text"
     },
     "scene.frame_url": {
       "type": "keyword"
     },
     "scene.frame_num": {
       "type": "integer"
     },
     
     "text": {
       "type": "text"
     },
     "text_elser.tokens": {
        "type": "rank_features" 
      },
      
     "speaker.id": {
       "type": "keyword"
     },
     
     "start": {
       "type": "float"
     },
     "end": {
       "type": "float"
     }
     
   }
 }
}

DELETE _ingest/pipeline/clauses-embeddings
PUT _ingest/pipeline/clauses-embeddings
{
 "description": "Clauses embedding pipeline",
 "processors": [
   {
      "inference": {
        "model_id": ".elser_model_1",
        "target_field": "text_elser",
        "field_map": { 
          "text": "text_field"
        },
        "inference_config": {
          "text_expansion": { 
            "results_field": "tokens"
          }
        }
      }
    }
 ],
 "on_failure": [
   {
     "set": {
       "description": "Index document to 'failed-<index>'",
       "field": "_index",
       "value": "failed-{{{_index}}}"
     }
   },
   {
     "set": {
       "description": "Set error message",
       "field": "ingest.failure",
       "value": "{{_ingest.on_failure_message}}"
     }
   }
 ]
}

DELETE /voices
PUT /voices
{
 "mappings": {
   "properties": {
     "example.url": {
       "type": "keyword"
     },
     "example.start": {
       "type": "float"
     },
     "example.stop": {
       "type": "float"
     },
     
     "speaker.name": {
       "type": "keyword"
     },
     "speaker.title": {
       "type": "keyword"
     },
     "speaker.company": {
       "type": "keyword"
     },
     "speaker.email": {
       "type": "keyword"
     },
     
     "voice_vector": {
       "type": "dense_vector",
       "dims": 192,
       "index": true,
       "similarity": "cosine"
     }
   }
 }
}
```

## Media Processing Instance

I selected a `g4dn.xlarge` EC2 instance type with a single NVIDIA T4 Tensor Core to handle the ML portion of this workload. I found this provided a good balance between cost (~ 0.50 per minute) and CPU/GPU power (processing ~1 hour of video in about 10 minutes). That said, this demo should run in any modern CUDA-powered environment. I created a 500GB root volume to contain the requisite ML models and temporary media. I used the Ubuntu 22 LTS AMI.

### Install Dev Tools

Some of the dependencies require build tooling to be available.

```
sudo apt update 
sudo apt install build-essential
```

### Install Docker

https://docs.docker.com/engine/install/ubuntu/

https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

sudo docker run --rm --runtime=nvidia --gpus all --env-file vars.env -v $PWD/prj:/prj -v /usr/local/cuda:/usr/local/cuda -v $PWD/../ingest:/ingest 48ff35cd9e8e2b488b4c1538965071f078c1ab1352cc0a2152ec909971626d52 /ingest/digikey-dip.mp4 04/19/23 "DIP Switches 101" tutorial digikey

### Install NVIDIA GPU Drivers

You will need to install NVIDIA GPU drivers and CUDA libraries for your selected GPU. In my case, I used the following:

```
mkdir -p ~/support/nvidia
cd ~/support/nvidia
wget https://us.download.nvidia.com/tesla/470.199.02/NVIDIA-Linux-x86_64-515.65.01.run
chmod a+x NVIDIA-Linux-x86_64-515.65.01.run
sudo ./NVIDIA-Linux-x86_64-515.65.01.run
```

```
wget https://developer.download.nvidia.com/compute/cuda/11.7.1/local_installers/cuda_11.7.1_515.65.01_linux.run
sudo sh cuda_11.7.1_515.65.01_linux.run
```

See https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/install-nvidia-driver.html for more info regarding installation of GPU drivers on EC2 instances.


### Install Anaconda

We use Anacoda ("conda") to manage our Python environment:

```
mkdir -p ~/support/anaconda
cd ~/support/anaconda
wget https://repo.anaconda.com/archive/Anaconda3-2023.03-1-Linux-x86_64.sh
chmod a+x Anaconda3-2023.03-1-Linux-x86_64.sh
./Anaconda3-2023.03-1-Linux-x86_64.sh
```

You will need to exit and re-enter your ssh session for the conda environment to be in effect.

### Download Source

```
cd ~
git clone https://github.com/ty-elastic/intheirownwords.git
cd intheirownwords
```

### Create and Activate Python Environment

Create a new Python 3.10 environment via:
```
conda create --name intheirownwords python=3.10
conda env config vars set CUDA_HOME="/usr/local/cuda"
```

Once the environment is created, you will need to activate it via `conda activate intheirownwords` with each new shell instance.

### Install Dependencies

```
# base dependencies for pytorch
conda install pytorch==2.0.0 torchvision==0.15.0 torchaudio==2.0.0 pytorch-cuda=11.7 -c pytorch -c nvidia

# install tesseract binaries
conda install -c conda-forge tesseract

# install required python libs
pip install git+https://github.com/pyannote/pyannote-audio.git@develop
pip install -r requirements.txt
```

### Environment Variables

Create a local shell script (`vars.sh`) to define the following variables:

```
# for s3 storage of ingested video and image files
export AWS_DEFAULT_REGION=""
export AWS_ACCESS_KEY_ID=""
export AWS_SECRET_ACCESS_KEY=""
export AWS_S3_BUCKET=""

# for huggingface models
export HF_TOKEN=""

# for export to elasticsearch
export ES_ENDPOINT="" # copied from Elastic Cloud Deployments page
export ES_USER="elastic"
export ES_PASS="" # password provided upon Elastic Cloud instance creation

# local disk temp prj directory
export PROJECT_DIR="./prj"
```

And export those variables with each new shell instance (`source vars.sh`).

## Run

### Content Ingest

```
conda activate intheirownwords
source ./vars.sh
python main.py content_path content_date content_name content_type content_source
```

### Search

```
conda activate intheirownwords
source ./vars.sh
streamlit run ui.py
```

# Future Work
* Dockerfile
* Detect slides in video
  * use motion detection to determine part of video not moving
  * use EAST text block detection to find a group of text blocks in non-moving video
  * use EAST text block detection to ignore very dense groups of text blocks (probably a demo)
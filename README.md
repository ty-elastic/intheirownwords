# In Their Own Words

An exemplary project to demonstrate the art-of-the-possible for search of informative video using off-the-shelf ML models and Elasticsearch ELSER semantic search!

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

## Media Processing Instance

I selected a `g4dn.xlarge` EC2 instance type with a single NVIDIA T4 Tensor Core to handle the ML portion of this workload. I found this provided a good balance between cost (~ 0.50 per minute) and CPU/GPU power (processing ~1 hour of video in about 10 minutes). That said, this demo should run on any modern CUDA-powered environment. I created a 500GB root volume to contain the requisite ML models and temporary media. I used the Ubuntu 22 LTS AMI.

### Setup environment vars

Create a file in your home directory on the Media Processing Instance with the following environment variables:

```
# for media storage
AWS_S3_BUCKET=

#for huggingface models
HF_TOKEN=

#for export to elasticsearch
ES_ENDPOINT=
ES_USER=
ES_PASS=

#optional if you want to use OpenAI for Q&A
OPENAI_API_KEY=
OPENAI_BASE=
OPENAI_DEPLOYMENT_ID=
OPENAI_MODEL=
OPENAI_API_VERSION=
```

### Install Dependencies

```
git clone https://github.com/ty-elastic/intheirownwords.git
cd intheirownwords/setup
./ubuntu.sh
./es.sh
```

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
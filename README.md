# In Their Own Words

An exemplary project to demonstrate the art-of-the-possible for search of informative video using off-the-shelf ML models and Elasticsearch ELSER semantic search!

## Background

Modern organizations, from large enterprises to school districts, share a lot of pertinent and timely information through video content (e.g., Town Halls, Tutorials, Webinars, Board Meetings). Typically such content addresses a wide range of topics within a given video, with each topic of interest only to a specific subset of the audience. Without a good intra-video search option, viewers are forced to consume such content linearly. At best, this potentially wastes a viewer's valuable time; at worst, it creates enough of a barrier to consumption that pertinent information (which could be a catalyst to further productivity) goes unwatched.

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

# Deployment

## Hugging Face Models

Some of the models require a [Hugging Face](https://huggingface.co) token and acceptance of respective user agreements. 

1. [Create a Hugging Face account](https://huggingface.co/join)
2. [Generate a token](https://huggingface.co/settings/tokens)
3. Accept the user agreement for the following models: [Segmentation](https://huggingface.co/pyannote/segmentation), [Voice Activity Detection (VAD)](https://huggingface.co/pyannote/voice-activity-detection), and [Speaker Diarization](https://huggingface.co/pyannote/speaker-diarization).

## Elastic Instance

You will need a modern Elastic (>= 8.9) instance with sufficient ML resources (at least 4GB of RAM) to support this demo. You can start a 2 week free trial of Elastic Cloud [here](https://cloud.elastic.co/registration). Be sure to select "4 GB RAM" for the Machine Learning instance type. When you create the instance, you will be provided a password for the `elastic` user; make note of it. Additionally, from the Deployments page, you will need the endpoint of your Elasticsearch instance.

## Media Storage

Because many content sites do not permit anonymous, external playback of video, this demo will upload your ingested video to a publicly-accessible s3 bucket to enable the UI to later play it back. The s3 bucket is assumed to be available in the same region as your EC2 Instance. You will need to setup the bucket with:
* [anonymous read permissions and static https hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/HostingWebsiteOnS3Setup.html)
* [an IAM allowing write permissions from your s3 instance](https://repost.aws/knowledge-center/ec2-instance-access-s3-bucket)

Obviously, for production use cases, you would likely host your own video content; the demo could be [modified accordingly](https://github.com/ty-elastic/intheirownwords/blob/1e4dbef4d48b35cffc146da860b778485137a950/src/prj.py#L53).

## EC2 Instance(s)

You can optionally run media ingest separately from the UI. This would enable you to run the more expensive GPU-enabled media ingest on-demand, with the UI running on a lesser (free!) compute tier. This documentation assumes a combined ingest and UI server.

I selected a `g4dn.xlarge` EC2 instance type with a single NVIDIA T4 Tensor Core to accommodate the ML required for ingest processing. I found this instance type provided a good balance between cost (~ 0.50 per minute) and CPU/GPU power (processing ~1 hour of video in about 10 minutes). That said, this demo should run on any modern CUDA-powered environment. I created a 500GB root volume to contain the requisite ML models and temporary media. The installation script assumes use of the Ubuntu 22 LTS AMI.

If this same EC2 instance will be serving the UI, you will need to update the inbound security rules to allow port `8501` from any host.

### Download the project

```
git clone https://github.com/ty-elastic/intheirownwords.git
cd intheirownwords
```

### Setup environment vars

Create a file named `env.vars` in the `/home/ubuntu/intheirownwords/` directory on the EC2 instance with the following environment variables:

```
# for media storage
AWS_S3_BUCKET=

#for huggingface models
HF_TOKEN=

#for export to elasticsearch
ES_ENDPOINT=
ES_USER=
ES_PASS=
```

### Install Dependencies

The following will setup dependencies on your EC2 instance to run the demo using docker containers. It will also setup requisite dependencies within Elasticsearch.

```
cd /home/ubuntu/intheirownwords/setup
./ubuntu.sh
./es.sh
```

If you intend to further develop this demo, you can run `./ubuntu.sh -d true` which will install the tools required to run directly on the host.

If you want to install and run just the UI on a separate EC2 instance (without a GPU), you can run `./ubuntu.sh -u true` which will skip installation of GPU-related tooling.

# Use

## Content Ingest

### Media Prep

Because many content sites do not permit anonymous, external playback of video, and because of the variety of formats possible, this demo requires you to externally download video, possibly transcode it (to a format ingestible by ffmpeg), and then upload it to your EC2 instance.

I have found the [HLS Downloader extension for Chrome](https://webextension.org/listing/hls-downloader.html) to be a reasonably good way of downloading exemplary video content from web sites. 1280x720p is generally a good resolution choice (higher resolution => longer processing time, but better slide OCR). In some instances, you may need to use `ffmpeg` to combine seperate video and audio renditions.

After you have a `.mkv` or `.mp4` file, upload it to your EC2 instance into the `/home/ubuntu/intheirownwords/ingest` folder. 

### Process and Ingest

Execute the following commands, where:
| Field                 | Description                           |
| --------------------  | ------------------------------------- |
| (ingest path)         | relative path (starting with /home/ubuntu/intheirownwords) to media file to ingest |
| (original source url) | URL from where the media was scrapped; useful when later tagging speakers/voices |
| (date) | date when video was recorded |
| (title) | video title |
| (type) | type of content (e.g., webinar); could be used to filter in UI |
| (origin) | origin of content (e.g., "elastic"); useful for multi-tenant setups |

```
cd /home/ubuntu/intheirownwords
./ingest-run.sh (ingest path) (original source url) (date) (title) (type) (origin)
```

example: `./ingest-run.sh ingest/test.mp4 http://elastic.co/blog/test 07/27/23 test webinar elastic`

## Search

Execute the following command:

```
cd /home/ubuntu/intheirownwords
./ui-run.sh
```

and browse to the External URL provided (remember to open port 8501 on your EC2 instance).

The search returns the relevant video, cued to the relevant section, with the relevant quote. It also uses a simple Q&A model (hosted on Elasticsearch) to try to extract a specific answer to the question provided. It further extracts the containing sentence for context.

## Voice ID

This demo uses Elasticsearch as a vector database to associate "voice prints" with speaker metadata. This allows the system to automatically tag repeat speakers in videos. After ingest, start the UI, and go to the "voices" tab on the left. Update each unknown speaker with associated metadata. The speaker metadata is linked at search time; you do not need to reimport videos after tagging.

# Future Work

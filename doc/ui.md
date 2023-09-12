# In Their Own Words

An exemplary project to demonstrate the art-of-the-possible for search of informative video using off-the-shelf ML models, Elasticsearch ELSER semantic search, Elasticsearch vector search for non-text media (audio), and Elasticsearch Reciprocal Rank Fusion (RRF)!

# Getting Started

1. Add a new Collection (Edit Collections > Create New Collection)
2. Import Video(s) from YouTube or local files
3. Wait for video to import (Import Status)
3. (optional) Assign Voices to Speakers
4. Search

## Rules and Regulations

* Upload only content publicly available from a customer's website. Do not upload anything confidential or under NDA.
* Do not upload any Elastic internal content (e.g., internal meetings)

# Example Demo Queries (By Collection)

## Elastic

* "what is elser?"
* "what is vector search useful for?"
* "what is RRF?"
* "is elser english only?"
* "when should i use an otel agent?"
* "what is open telemetry?"
* "how does otel logging work?"
* "how do i instrument apm on kubernetes?"

## Park Ridge-Niles School District 64

* "who resigned?"
* "are we buying new chromebooks?"
* "is construction at washington done?"
* "how many kids are in kindergarten?"

## Bloomington Public Schools, MN

* "when does school start?"
* "how is bec-tv funded?"

# FAQ

## How much would this cost?

This PoC comprises 3 logical elements:
1. A relatively small (scales with text ingested) Elasticsearch instance with ML nodes for ELSER and Q&A models (auto-scale is recommended for ML nodes)
2. A frontend search UI based on Streamlit which can run on some trivially small linux instance
3. An on-demand ingest processor which performs speech-to-text, diarization, and optical character recognition one-time on media ingest

Note that the PoC currently runs (2) and (3) on the same node, though in practice, they are unique docker containers and could easily be seperated. Further, (3) could theoretically be auto-scaled using k8s, for example.

Regarding (3), a GCP n1-standard-4 (4 vCPU, 2 core, 15GB RAM) with a single Tesla T4 GPU can process roughly 1 hour of content in ~10 minutes. This works out to ~$0.10 per hour of video ingested.

# APIs

## Search

`GET /search`

| Request Argument | Optional? | Type     | Description                                    |
| ---------------- | --------- | -------- | ---------------------------------------------- |
| x-api-key        | N         | string   | API key                                        |
| origin           | N         | string   | collection name                                |
| query            | N         | string   | text to search on                              |
| size             | Y         | int      | number of search results to return (default=1) |
| kinds            | Y         | string   | limit search to specific media kinds           |

### cURL Example

```
curl -X GET -G 'https://videos.corp-intranet.com/search' --data-urlencode 'x-api-key=abc123' --data-urlencode 'origin=Park Ridge-Niles School District 64' --data-urlencode 'query=who resigned?' --data-urlencode 'kinds=School Board Meeting' --data-urlencode 'size=1'
```

```
[
    {
        'date': '2023-04-20T00: 00: 00.000Z', 
        'speaker.name': 'Dr. Bob Smith',
        'speaker.title': 'Superintendent',
        'speaker.company': 'Park Ridge-Niles School District 64',
        'speaker.email': 'bob.smith@d64.org',
        'kind': 'School Board Meeting', 
        'media.url': 'https: //storage.googleapis.com/intheirownwords/projects/221b6de7-d535-4fda-920a-8a368a7932d9/221b6de7-d535-4fda-920a-8a368a7932d9.mp4?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=intheirownwords%40elastic-sa.iam.gserviceaccount.com%2F20230906%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20230906T184246Z&X-Goog-Expires=86400&X-Goog-SignedHeaders=host&X-Goog-Signature=5085425b2d3be9edbfe83a86d1aca36088b02daa83d9c49b29d73747c73dc26d029ba4db0e5d024758532cb00fe2b75896155294489587e05c18145c2ce0330551e9751426c8d2ef424cd56b2f43220a1ae2353bfacdaf838da9ccc61f0b060a187eb3546c588198b4e0f68b4887817f2b78aee2786d366741a627de4abec118640af8c74de970c90f09504bd60472bf1169f401500c9d9090dd886b19b59ead03a2d5f8ef0969c71c2eb5fea2c3b2a183c4342b692e01ab0b25ea83ab8492a7d74b5dc11d6d440a78f648aeb606157676e3ef1e6ca338ff96306c5b9bb4dec85a77c98f1146b4a843e2cff8acdb075d6005ad16f1960456ea2412b37d46a02b', 
        'media.start': 2545.701, 
        'media.end': 2558.149, 
        'origin': 'Park Ridge-Niles School District 64', 
        'text': "Well, two resignations that are tough on there are Sarah Jones and Mary O'Brien. We wish them well, but those are tough ones on this report. Okay, why don't we take the motion?",
        'scene.frame_text': 'STAFF UPDATES'
        'title': '2023-04-20', 
        'source_url': 'https://www.d64.org/boe/bd-of-ed-archives-january-23-june-23', 
        'answer.text': 'Sarah Jones and Mary O'Brien', 
        'answer.start': 51, 
        'answer.stop': 78, 
        'confidence': 13.426591
    }
]
```

### Python Example

```
import requests
resp = requests.get("https://videos.corp-intranet.com/search", params={'x-api-key': 'abc123', 'origin': 'Park Ridge-Niles School District 64', 'query': 'who resigned?'})
print(resp.json())
```

```
[
    {
        'date': '2023-04-20T00: 00: 00.000Z', 
        'speaker.name': 'Dr. Bob Smith',
        'speaker.title': 'Superintendent',
        'speaker.company': 'Park Ridge-Niles School District 64',
        'speaker.email': 'bob.smith@d64.org',
        'kind': 'School Board Meeting', 
        'media.url': 'https: //storage.googleapis.com/intheirownwords/projects/221b6de7-d535-4fda-920a-8a368a7932d9/221b6de7-d535-4fda-920a-8a368a7932d9.mp4?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=intheirownwords%40elastic-sa.iam.gserviceaccount.com%2F20230906%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20230906T184246Z&X-Goog-Expires=86400&X-Goog-SignedHeaders=host&X-Goog-Signature=5085425b2d3be9edbfe83a86d1aca36088b02daa83d9c49b29d73747c73dc26d029ba4db0e5d024758532cb00fe2b75896155294489587e05c18145c2ce0330551e9751426c8d2ef424cd56b2f43220a1ae2353bfacdaf838da9ccc61f0b060a187eb3546c588198b4e0f68b4887817f2b78aee2786d366741a627de4abec118640af8c74de970c90f09504bd60472bf1169f401500c9d9090dd886b19b59ead03a2d5f8ef0969c71c2eb5fea2c3b2a183c4342b692e01ab0b25ea83ab8492a7d74b5dc11d6d440a78f648aeb606157676e3ef1e6ca338ff96306c5b9bb4dec85a77c98f1146b4a843e2cff8acdb075d6005ad16f1960456ea2412b37d46a02b', 
        'media.start': 2545.701, 
        'media.end': 2558.149, 
        'origin': 'Park Ridge-Niles School District 64', 
        'text': "Well, two resignations that are tough on there are Sarah Jones and Mary O'Brien. We wish them well, but those are tough ones on this report. Okay, why don't we take the motion?",
        'scene.frame_text': 'STAFF UPDATES'
        'title': '2023-04-20', 
        'source_url': 'https://www.d64.org/boe/bd-of-ed-archives-january-23-june-23', 
        'answer.text': 'Sarah Jones and Mary O'Brien', 
        'answer.start': 51, 
        'answer.stop': 78, 
        'confidence': 13.426591
    }
]
```

## Upload Media

`GET /upload`

*(we use GET becaused of the hacked up way we add arbitrary handlers to Streamlit)*

| Request Argument | Optional? | Description                                    |
| ---------------- | --------- | ---------------------------------------------- |
| x-api-key        | N         | API key                                        |

| JSON Body Field  | Optional? | Description                                    |
| ---------------- | --------- | ---------------------------------------------- |
| youtube_url      | Y         | URL to YouTube video                           |
| media_url        | Y         | URL to arbitrary video                         |
| title            | N         | title of video                                 |
| date             | N         | date video was recorded in 2023-09-06 format   |
| kind             | N         | kind/type of video                             |
| origin           | N         | collection                                     |

## Create Origin

`GET /origin`

*(we use GET becaused of the hacked up way we add arbitrary handlers to Streamlit)*

| Request Argument | Optional? | Description                                    |
| ---------------- | --------- | ---------------------------------------------- |
| x-api-key        | N         | API key                                        |

| JSON Body Field  | Optional? | Description                                    |
| ---------------- | --------- | ---------------------------------------------- |
| kinds            | N         | array of kinds/types of video                  |
| origin           | N         | collection                                     |
| homepage_url     | N         | URL to page of collection/org                  |
| logo_url         | Y         | URL to logo                                    |
| results.size     | Y         | number of results to return by default         |

# Technology Stack

* Speech-to-Text and Diarization: [WhisperX](https://github.com/m-bain/whisperX)
* OCR: [Tesseract](https://github.com/tesseract-ocr/tesseract)

# Concept of Operations

## Ingest

1. Convert audio to paragraphs
    1. Extract audio from file
    2. Generate text sentences from speech (STT)
    3. Assign speakers to sentences (diarization)
        1. Generate embedding for voice
        2. Search for embedding in Elasticsearch using kNN
        3. If no match, create new voice record in Elasticsearch
    4. Group sentences
        1. By speaker
        2. By "thought" (using sentence similarity model)
        3. Split if greater than ELSER token limit
2. Convert slides (if present) to keywords
    1. Extract video frames from file
    2. Compare frames looking for unique frames
    3. Apply Optical Character Recognition (OCR) to unique frames
    4. Keep only unique, high-confidence frame text
3. Align and merge extracted frame text with "thoughts" (from step 4) to create clauses
4. Store clauses in Elasticsearch

## Search

1. Extract keywords from query
2. Submit query (ELSER against clause text) and keywords (BM25 against clause text and associated frame text) to Elasticsearch for a hybrid query (this is used to obtain a minimum score; if it is below a threshold, return no results)
3. Submit query (ELSER against clause text) and keywords (BM25 against clause text and associated frame text) to Elasticsearch for a RRF query
4. Run RRF results through a Q&A model (running on Elasticsearch ML nodes) to highlight answer

# Background

Modern organizations, from large enterprises to school districts, share a lot of pertinent and timely information through video content (e.g., Town Halls, Tutorials, Webinars, Board Meetings). Typically such content addresses a wide range of topics within a given video, with each topic of interest only to a specific subset of the audience. Without a good intra-video search option, viewers are forced to consume such content linearly. At best, this potentially wastes a viewer's valuable time; at worst, it creates enough of a barrier to consumption that pertinent information (which could be a catalyst to further productivity) goes unwatched.

In general, few options exist to make informative, often private (e.g., internal use only), video practically searchable. Some existing projects summarize video content using a public Speech-To-Text (STT) engine and LLM (e.g., as offered by OpenAI), and then offer search on top of the summarized output. Use of such services, however, potentially puts private information at risk for public exposure. Further, and arguably more importantly, speakers in informative video are generally:
* subject matter experts
* well-spoken
* already producing expertly-curated summarized content

Adding a LLM to summarize their carefully chosen words can easily skew their intended meaning. As an example, consider a company townhall meeting which includes a discussion from the VP of HR regarding a layoff: the words spoken have been carefully selected and their nuance matters. This project (as the name implies) intentionally forgoes such paraphrasing and instead lets subject matter experts speak for themselves.

## Tenets

* Don’t trust a LLM to summarize critical information; let people speak for themselves
* Don’t share private data with a hosted AI service

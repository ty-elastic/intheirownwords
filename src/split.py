import numpy as np
import string
import es_ml
from sentence_transformers import SentenceTransformer, util
import pandas as pd
from functools import reduce

MAX_THOUGHT_INTERRUPT = 2
SIMILARITY_THRESHOLD = 0.4

SCENE_OVERLAP = 3
ELSER_TOKEN_LIMIT = 512

sentence_sim_model = SentenceTransformer('all-MiniLM-L6-v2')

def find_scene(project, start, end):
    for scene in project['scenes']:
        start_overlap = 0
        if scene['start'] > SCENE_OVERLAP:
            start_overlap = SCENE_OVERLAP
        if start >= (scene['start']-start_overlap) and end > scene['start'] and end <= (scene['end']+SCENE_OVERLAP):
            return scene
    return None

def create_clause(chunk, segment, project):
    clause = {'speaker.id':chunk['speaker_id'], 'scene.frame_num':None, 'start': segment['start'], 'end': segment['end']}
    scene = chunk['scene']
    if scene != None:
        clause['scene.frame_num']:['frame_num']
        clause['scene.start'] = scene['start']
        clause['scene.end'] = scene['end']
        if 'frame_text' in scene:
            clause['scene.frame_text'] = scene['frame_text']
        clause['scene.frame_url'] = scene['frame_url']        
        clause['scene.frame_num'] = scene['frame_num']  
    clause['project_id'] = project['id']
    clause['media_url'] = project['media_url']
    clause['title'] = project['title']
    clause['date'] = project['date'].strftime('%Y-%m-%d')
    clause['kind'] = project['kind']
    clause['origin'] = project['origin']
    clause['source_url'] = project['source_url']

    clause['text'] = " ".join(segment['text'])
    return clause

def split_chunk(chunk, clauses, project):
    # print("---PRE")
    # print(chunk['segments'])
    chunk_segments = chunk_text(chunk['segments'])
    # print("---POST")
    # print(chunk_segments)

    clause = None
    for chunk_segment in chunk_segments:
        clause = create_clause(chunk, chunk_segment, project)
        clauses.append(clause)

def split(project, segments):
    clauses = []
    chunk = None

    print(f"segments={len(segments)}")
    for i, segment in enumerate(segments):
        #print(segment)
        scene = find_scene(project, segment['start'], segment['end'])
        if chunk is None:
            chunk = {'speaker_id':segment['speaker_id'], 'segments':[], 'scene':scene}
        elif (segment['speaker_id'] != chunk['speaker_id']): # or (scene is not chunk['scene']):
            print("split by speaker change")
            split_chunk(chunk, clauses, project)
            chunk = {'speaker_id':segment['speaker_id'], 'segments':[], 'scene':scene}
        chunk['segments'].append(segment)
    if chunk != None:
        split_chunk(chunk, clauses, project)

    project['clauses'] = clauses
    # print(clauses)
    return clauses

def chunk_text(segments):
    df = pd.DataFrame(segments)

    # Split text to sentences and get their embedding
    embeddings = create_embedding(df['text'])

    # Get the points where we need to split the text
    true_middle_points = get_cut_points(embeddings)
    #print(true_middle_points)
    # Initiate text to append to
    segments = []
    thought = None
    for num, segment in df.iterrows():
        if thought == None:
            thought = {"start":segment.start, "text":[]}
        elif np.isin(num, true_middle_points):
            print("split by thought")
            segments.append(thought)
            thought = {"start":segment.start, "text":[]}
        elif reduce(lambda x, y: x + count_words(y), thought['text'], 0)+count_words(segment.text) >= ELSER_TOKEN_LIMIT:
            print("split by length")
            if len(thought['text']) > 0:
                segments.append(thought)
            thought = {"start":segment.start, "text":[]}
        thought['text'].append(segment.text.strip())
        thought['end'] = segment.end
    if thought is not None:
        segments.append(thought)
    #print(segments)
    return segments

def create_embedding(sentences):
    # Encode the sentences using the model
    embeddings = sentence_sim_model.encode(sentences)
    return embeddings

def count_words(sentence):
    return sum([i.strip(string.punctuation).isalpha() for i in sentence.split()])

def get_next_cut(remaining_sims):
    dissim_start = []
    for i, sim in enumerate(remaining_sims):
        if sim < SIMILARITY_THRESHOLD: 
            if len(dissim_start) >= MAX_THOUGHT_INTERRUPT:
                return dissim_start[0]+1
            # allow up to MAX_THOUGHT_INTERRUPT non-related sentences in between 2 related sentences
            else:
                dissim_start.append(i)
        else:
            dissim_start = []
    if len(dissim_start) > 0:
        return dissim_start[0]+1

def get_remaining_sims(embeddings, start): 
    similarities = []
    for i in range(start+1, len(embeddings)):
        similarities.append(util.cos_sim(embeddings[start], embeddings[i]))
    return similarities

def get_cut_points(embeddings:np.array) -> list:
    cut_points = []
    i = 0
    while True:
        if i >= len(embeddings)-1:
            break

        remaining_sims = get_remaining_sims(embeddings, i)
        cut_point = get_next_cut(remaining_sims)
        if cut_point is None:
            break
        i = cut_point + i
        cut_points.append(i)
    #print(cut_points)
    return cut_points

# test = "Hi I'm a banana. The federal government has released enough food and water to support to 5,000 people for five days as part of the ongoing response to the devastating Hawaii wildfires, a White House spokesperson said Friday. The Federal Emergency Management Agency is continuing to work on providing more shelter supplies, such as water, food and blankets, for people impacted in the state, the spokesperson added. The Coast Guard, Navy National Guard and Army are all working to support response and rescue efforts.  The United States Department of Agriculture has also established a Type 3 Incident Management Team and is supporting requests from the state for wildfire liaisons. President Joe Biden issued a federal disaster declaration on Thursday, promising to send whatever is needed to help the recovery. Assistance from the declaration can include grants for temporary housing and home repairs, low-cost loans to cover uninsured property losses and other programs to help with recovery. Now let's talk about computers. I like to eat toothpaste. Toothpaste is great for teeth. PCs are amazing machines."
# ss = es_ml.split_sentences(test)
# segments = []
# for i, s in enumerate(ss):
#     segment = {"start": i, "end":i, "text":s}
#     segments.append(segment)
# chunk_segments = chunk_text(segments)

# print("---POST")
# for seg in chunk_segments:
#     print(seg)
#     print(" --")

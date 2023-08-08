import numpy as np
# Library to import pre-trained model for sentence embeddings
# Calculate similarities between sentences
from sklearn.metrics.pairwise import cosine_similarity
# package for finding local minimas
from scipy.signal import argrelextrema
import math

from sentence_transformers import SentenceTransformer
import pandas as pd
from functools import reduce

MAX_P_SIZE=10
SCENE_OVERLAP = 3
ELSER_TOKEN_LIMIT = 512

# inspired by https://github.com/poloniki/quint

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
    print("---PRE")
    print(chunk['segments'])
    chunk_segments = chunking_text(chunk['segments'])
    print("---POST")
    print(chunk_segments)

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
        elif (scene is not chunk['scene']) or (segment['speaker_id'] != chunk['speaker_id']):
            print("split by thought or speaker change")
            split_chunk(chunk, clauses, project)
            chunk = {'speaker_id':segment['speaker_id'], 'segments':[], 'scene':scene}
        chunk['segments'].append(segment)
    if chunk != None:
        split_chunk(chunk, clauses, project)

    project['clauses'] = clauses
    print(clauses)
    return clauses

def chunking_text(segments):
    df = pd.DataFrame(segments)

    # Split text to sentences and get their embedding
    embeddings = create_embedding(df['text'])

    # Get the points where we need to split the text
    true_middle_points = get_middle_points(embeddings)
    # Initiate text to append to
    segments = []
    thought = None
    for num, segment in df.iterrows():
        if thought == None:
            thought = {"start":segment.start, "text":[]}
        elif np.isin(num, true_middle_points) or reduce(lambda x, y: x + len(y), thought['text'], 0)+len(segment.text) >= ELSER_TOKEN_LIMIT:
            segments.append(thought)
            thought = {"start":segment.start, "text":[]}
        thought['text'].append(segment.text.strip())
        thought['end'] = segment.end
    if thought is not None:
        segments.append(thought)
    #print(segments)
    return segments

def rev_sigmoid(x:float)->float:
    return (1 / (1 + math.exp(0.5*x)))

def activate_similarities(similarities:np.array, p_size)->np.array:
        """ Function returns list of weighted sums of activated sentence similarities
        Args:
            similarities (numpy array): it should square matrix where each sentence corresponds to another with cosine similarity
            p_size (int): number of sentences are used to calculate weighted sum
        Returns:
            list: list of weighted sums
        """
        # To create weights for sigmoid function we first have to create space. P_size will determine number of sentences used and the size of weights vector.
        x = np.linspace(-10,10,p_size)
        # Then we need to apply activation function to the created space
        y = np.vectorize(rev_sigmoid)
        # Because we only apply activation to p_size number of sentences we have to add zeros to neglect the effect of every additional sentence and to match the length ofvector we will multiply
        activation_weights = np.pad(y(x),(0,similarities.shape[0]-p_size))
        ### 1. Take each diagonal to the right of the main diagonal
        diagonals = [similarities.diagonal(each) for each in range(0,similarities.shape[0])]
        ### 2. Pad each diagonal by zeros at the end. Because each diagonal is different length we should pad it with zeros at the end
        diagonals = [np.pad(each, (0,similarities.shape[0]-len(each))) for each in diagonals]
        ### 3. Stack those diagonals into new matrix
        diagonals = np.stack(diagonals)
        ### 4. Apply activation weights to each row. Multiply similarities with our activation.
        diagonals = diagonals * activation_weights.reshape(-1,1)
        ### 5. Calculate the weighted sum of activated similarities
        activated_similarities = np.sum(diagonals, axis=0)
        return activated_similarities

def get_middle_points(embeddings:np.array) -> list:
    # Create similarities matrix
    similarities = cosine_similarity(embeddings)

    p_size = MAX_P_SIZE
    if p_size > similarities.shape[0]:
        p_size = similarities.shape[0]

    # Let's apply our function. For long sentences i reccomend to use 10 or more sentences
    activated_similarities = activate_similarities(similarities, p_size=p_size)

    ### 6. Find relative minima of our vector. For all local minimas and save them to variable with argrelextrema function
    minmimas = argrelextrema(activated_similarities, np.less, order=2) #order parameter controls how frequent should be splits. I would not reccomend changing this parameter.
    return minmimas

def create_embedding(sentences):
    # Encode the sentences using the model
    embeddings = sentence_sim_model.encode(sentences)
    return embeddings

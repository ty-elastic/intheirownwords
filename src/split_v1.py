import string
from sentence_transformers import SentenceTransformer, util

MAX_THOUGHT_INTERRUPT = 1
SIMILARITY_THRESHOLD = 0.5

ELSER_TOKEN_LIMIT = 512

#sentence_sim_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
sentence_sim_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def chunk_text(segments):
    for segment in segments:
        #print(segment)
        segment['word_count'] = count_words(segment['text'])
        segment['embedding'] = sentence_sim_model.encode(segment['text'])

    #print(segments)

    # Get the points where we need to split the text
    cut_points = get_cut_points(segments)
    for segment in segments:
        del segment['embedding']

    # Initiate text to append to
    thoughts = []
    thought = None
    for num, segment in enumerate(segments):
        if thought == None:
            thought = {"start":segment['start'], "text":[]}
        elif num in cut_points:
            thoughts.append(thought)
            thought = {"start":segment['start'], "text":[]}
        thought['text'].append(segment['text'].strip())
        thought['end'] = segment['end']
    if thought is not None:
        thoughts.append(thought)
    # print(thoughts)
    return thoughts

def count_words(sentence):
    return sum([i.strip(string.punctuation).isalpha() for i in sentence.split()])

def get_next_cut(remaining_sims, eof):
    dissim_start = []
    for i, sim in enumerate(remaining_sims):
        #print(sim)
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
    elif eof:
        return None
    else:
        return len(remaining_sims)

def get_remaining_sims(segments, start): 
    similarities = []
    token_count = 0
    for i in range(start+1, len(segments)):
        if token_count + segments[i]['word_count'] >= ELSER_TOKEN_LIMIT:
            print("hit token limit")
            return similarities, False
        #print(f"{segments[start]['text']}, {segments[i]['text']}, {util.cos_sim(segments[start]['embedding'], segments[i]['embedding'])}")
        similarities.append(util.pytorch_cos_sim(segments[start]['embedding'], segments[i]['embedding']))
        token_count = token_count + segments[i]['word_count']
    return similarities, True

def get_cut_points(segments) -> list:
    cut_points = []
    i = 0
    while i < len(segments)-1:
        remaining_sims, eof = get_remaining_sims(segments, i)
        cut_point = get_next_cut(remaining_sims, eof)
        if cut_point is None:
            break
        i = cut_point + i
        cut_points.append(i)
    #print(cut_points)
    return cut_points
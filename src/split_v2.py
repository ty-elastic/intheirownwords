import numpy as np
import string

# Library to import pre-trained model for sentence embeddings
# Calculate similarities between sentences
from sklearn.metrics.pairwise import cosine_similarity
# package for finding local minimas
from scipy.signal import argrelextrema
import math

from sentence_transformers import SentenceTransformer
import pandas as pd
from functools import reduce

ELSER_TOKEN_LIMIT = 512

SPACE_SIZE = 5
MAX_P_SIZE = 5
ORDER = 1

# copied from https://github.com/poloniki/quint

sentence_sim_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def chunk_text(segments):
    df = pd.DataFrame(segments)
    embeddings = sentence_sim_model.encode(df['text'])

    # Get the points where we need to split the text
    true_middle_points = get_middle_points(embeddings)
    # Initiate text to append to
    segments = []
    thought = None
    for num, segment in df.iterrows():
        segment.text = segment.text.strip()
        if thought == None:
            thought = {"start":segment.start, "text":[]}
        elif np.isin(num, true_middle_points) or reduce(lambda sum,element:sum+count_words(element), thought['text'], 0)+count_words(segment.text) >= ELSER_TOKEN_LIMIT:
            segments.append(thought)
            thought = {"start":segment.start, "text":[]}
        thought['text'].append(segment.text)
        thought['end'] = segment.end
    if thought is not None:
        segments.append(thought)
    #print(segments)
    return segments

def count_words(sentence):
    return sum([i.strip(string.punctuation).isalpha() for i in sentence.split()])

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
        x = np.linspace(-SPACE_SIZE,SPACE_SIZE,p_size)
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
    minmimas = argrelextrema(activated_similarities, np.less, order=ORDER) #order parameter controls how frequent should be splits. I would not reccomend changing this parameter.
    return minmimas

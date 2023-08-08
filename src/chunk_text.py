
import numpy as np
# Library to import pre-trained model for sentence embeddings
# Calculate similarities between sentences
from sklearn.metrics.pairwise import cosine_similarity
# package for finding local minimas
from scipy.signal import argrelextrema
import math
import nltk.data
import nltk

nltk.download('punkt')

from sentence_transformers import SentenceTransformer
import pandas as pd

MAX_P_SIZE=10

# from https://github.com/poloniki/quint

model = SentenceTransformer('all-MiniLM-L6-v2')

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
        elif np.isin(num, true_middle_points):
            segments.append(thought)
            thought = {"start":segment.start, "text":[]}
        thought['text'].append(segment.text)
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
    embeddings = model.encode(sentences)
    return embeddings

# segments = []
# segments.append({'start': 7.745, 'end': 8.726, 'text': ' Hi.', 'words': [{'word': 'Hi.', 'start': 7.745, 'end': 7.945, 'score': 0.779, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}], 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'})
# segments.append({'start': 8.726, 'end': 16.189, 'text': "So today we're going to talk a little bit about a model that we trained, or fine-tuned rather, for text retrieval.", 'words': [{'word': 'So', 'start': 8.726, 'end': 9.046, 'score': 0.952, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'today', 'start': 9.706, 'end': 9.926, 'score': 0.813, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': "we're", 'start': 9.946, 'end': 10.046, 'score': 0.241, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'going', 'start': 10.066, 'end': 10.166, 'score': 0.402, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'to', 'start': 10.186, 'end': 10.246, 'score': 0.744, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'talk', 'start': 10.286, 'end': 10.426, 'score': 0.779, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'a', 'start': 10.446, 'end': 10.466, 'score': 0.975, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'little', 'start': 10.486, 'end': 10.647, 'score': 0.998, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'bit', 'start': 10.667, 'end': 10.787, 'score': 0.824, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'about', 'start': 10.827, 'end': 11.087, 'score': 0.832, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'a', 'start': 11.107, 'end': 11.127, 'score': 0.0, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'model', 'start': 11.887, 'end': 12.147, 'score': 0.951, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'that', 'start': 12.187, 'end': 12.287, 'score': 0.879, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'we', 'start': 12.307, 'end': 12.427, 'score': 0.984, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'trained,', 'start': 12.488, 'end': 12.968, 'score': 0.826, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'or', 'start': 13.208, 'end': 13.288, 'score': 0.978, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'fine-tuned', 'start': 13.348, 'end': 13.848, 'score': 0.504, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'rather,', 'start': 13.908, 'end': 14.208, 'score': 0.848, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'for', 'start': 14.228, 'end': 14.569, 'score': 0.665, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'text', 'start': 14.689, 'end': 14.929, 'score': 0.852, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'retrieval.', 'start': 14.969, 'end': 15.469, 'score': 0.746, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}], 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'})
# segments.append({'start': 16.189, 'end': 18.391, 'text': "And we're going to introduce the whole process.", 'words': [{'word': 'And', 'start': 16.189, 'end': 16.79, 'score': 0.581, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': "we're", 'start': 16.81, 'end': 16.93, 'score': 0.361, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'going', 'start': 16.97, 'end': 17.07, 'score': 0.462, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'to', 'start': 17.09, 'end': 17.17, 'score': 0.233, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'introduce', 'start': 17.19, 'end': 17.63, 'score': 0.822, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'the', 'start': 17.67, 'end': 17.73, 'score': 0.833, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'whole', 'start': 17.75, 'end': 17.89, 'score': 0.836, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'process.', 'start': 17.91, 'end': 18.351, 'score': 0.934, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}], 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'})
# segments.append({'start': 18.391, 'end': 21.112, 'text': 'Just before that, my name is Tom Vesey.', 'words': [{'word': 'Just', 'start': 18.391, 'end': 18.551, 'score': 0.9, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'before', 'start': 18.591, 'end': 18.871, 'score': 0.944, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'that,', 'start': 18.911, 'end': 19.151, 'score': 0.869, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'my', 'start': 19.831, 'end': 19.971, 'score': 0.867, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'name', 'start': 20.011, 'end': 20.152, 'score': 0.985, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'is', 'start': 20.212, 'end': 20.272, 'score': 0.597, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'Tom', 'start': 20.312, 'end': 20.472, 'score': 0.921, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'Vesey.', 'start': 20.512, 'end': 20.932, 'score': 0.513, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}], 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'})
# segments.append({'start': 21.112, 'end': 25.995, 'text': "I'm R&D lead on the machine learning team at Elastic.", 'words': [{'word': "I'm", 'start': 21.112, 'end': 21.252, 'score': 0.677, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'R&D', 'start': 21.692, 'end': 22.173, 'score': 0.565, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'lead', 'start': 22.673, 'end': 22.993, 'score': 0.891, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'on', 'start': 23.193, 'end': 23.293, 'score': 0.612, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'the', 'start': 23.333, 'end': 23.533, 'score': 0.924, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'machine', 'start': 23.673, 'end': 23.913, 'score': 0.738, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'learning', 'start': 23.933, 'end': 24.154, 'score': 0.575, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'team', 'start': 24.194, 'end': 24.394, 'score': 0.744, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'at', 'start': 24.434, 'end': 24.474, 'score': 0.592, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}, {'word': 'Elastic.', 'start': 24.494, 'end': 24.914, 'score': 0.77, 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'}], 'speaker': 'SPEAKER_01', 'speaker_id': 'L5uQ0YkBP9V0fSOrgiek'})
# segments.append({'start': 25.995, 'end': 30.477, 'text': "And I'm Quentin, and I'm a data scientist at Elastic for almost a year now.", 'words': [{'word': 'And', 'start': 25.995, 'end': 26.135, 'score': 0.658, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': "I'm", 'start': 26.475, 'end': 26.635, 'score': 0.57, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'Quentin,', 'start': 26.695, 'end': 27.075, 'score': 0.473, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'and', 'start': 27.395, 'end': 27.495, 'score': 0.782, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': "I'm", 'start': 27.575, 'end': 27.715, 'score': 0.744, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'a', 'start': 27.836, 'end': 27.856, 'score': 0.0, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'data', 'start': 27.936, 'end': 28.176, 'score': 0.414, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'scientist', 'start': 28.196, 'end': 28.676, 'score': 0.773, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'at', 'start': 28.696, 'end': 28.796, 'score': 0.718, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'Elastic', 'start': 29.116, 'end': 29.576, 'score': 0.775, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'for', 'start': 29.616, 'end': 29.757, 'score': 0.593, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'almost', 'start': 29.797, 'end': 30.057, 'score': 0.602, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'a', 'start': 30.077, 'end': 30.117, 'score': 0.438, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'year', 'start': 30.157, 'end': 30.317, 'score': 0.471, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}, {'word': 'now.', 'start': 30.357, 'end': 30.477, 'score': 0.469, 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'}], 'speaker': 'SPEAKER_02', 'speaker_id': 'MJuQ0YkBP9V0fSOrgyfd'})
# chunking_text(segments)
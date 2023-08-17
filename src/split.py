import numpy as np
import string
from sentence_transformers import SentenceTransformer, util
import es_clauses
import es_ml

MAX_THOUGHT_INTERRUPT = 2
SIMILARITY_THRESHOLD = 0.3

ELSER_TOKEN_LIMIT = 512

#sentence_sim_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
sentence_sim_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def find_scenes(project, voice_start, voice_end):
    scenes = []
    for scene in project['scenes']:
        # slide starts before voice, ends before voice
        if scene['start'] <= voice_start and scene['end'] <= voice_end and scene['end'] >= voice_start:
            scenes.append(scene)
        #slide starts before voice, ends after voice
        elif scene['start'] <= voice_start and scene['end'] >= voice_end:
            scenes.append(scene)
        # slide starts after voice, ends before voice
        elif scene['start'] >= voice_start and scene['end'] <= voice_end:
            scenes.append(scene)
        # slide starts after voice, ends after voice
        elif scene['start'] >= voice_start and scene['start'] <= voice_end and scene['end'] >= voice_end:
            scenes.append(scene)
    return scenes

def create_clause(chunk, segment, project):
    clause = {'speaker.id':chunk['speaker_id'], 'start': segment['start'], 'end': segment['end']}

    clause['scene.frame_num'] = []
    clause['scene.start'] = []
    clause['scene.end'] = []
    clause['scene.frame_text'] = []
    clause['scene.frame_url'] = []     
    clause['scene.frame_num'] = []

    scenes = find_scenes(project, segment['start'], segment['end'])
    #print(scenes)
    for scene in scenes:
        # print(scene['frame_num'])
        # print(clause['scene.frame_num'])
        if scene['frame_num'] not in clause['scene.frame_num']:
            clause['scene.frame_num'].append(scene['frame_num'])
            clause['scene.start'].append(scene['start'])
            clause['scene.end'].append(scene['end'])
            clause['scene.frame_text'].append(scene['frame_text'])
            if 'frame_url' in scene:
                clause['scene.frame_url'].append(scene['frame_url'])

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
    chunk_segments = chunk_text(chunk['segments'])
    print("---POST")
    print(chunk_segments)

    clause = None
    for chunk_segment in chunk_segments:
        clause = create_clause(chunk, chunk_segment, project)
        clauses.append(clause)

def split(project, segments):
    clauses = []
    chunk = None

    for segment in segments:
        print(segment)
        if chunk is None:
            chunk = {'speaker_id':segment['speaker_id'], 'segments':[], 'scenes':[]}
        elif (segment['speaker_id'] != chunk['speaker_id']): # or (scene is not chunk['scene']):
            print("split by speaker change")
            split_chunk(chunk, clauses, project)
            chunk = {'speaker_id':segment['speaker_id'], 'segments':[], 'scenes':[]}
        chunk['segments'].append(segment)
    if chunk != None:
        split_chunk(chunk, clauses, project)

    project['clauses'] = clauses
    # print(clauses)
    return clauses

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
        print(f"{segments[start]['text']}, {segments[i]['text']}, {util.cos_sim(segments[start]['embedding'], segments[i]['embedding'])}")
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

# test = "Hi I'm a banana. The federal government has released enough food and water to support to 5,000 people for five days as part of the ongoing response to the devastating Hawaii wildfires, a White House spokesperson said Friday. The Federal Emergency Management Agency is continuing to work on providing more shelter supplies, such as water, food and blankets, for people impacted in the state, the spokesperson added. The Coast Guard, Navy National Guard and Army are all working to support response and rescue efforts.  The United States Department of Agriculture has also established a Type 3 Incident Management Team and is supporting requests from the state for wildfire liaisons. President Joe Biden issued a federal disaster declaration on Thursday, promising to send whatever is needed to help the recovery. Assistance from the declaration can include grants for temporary housing and home repairs, low-cost loans to cover uninsured property losses and other programs to help with recovery. Now let's talk about computers. I like to eat toothpaste. Toothpaste is great for teeth. PCs are amazing machines."
# ss = es_ml.split_sentences(test + " " + test + " " + test + " " + test + " " + test + " " + test + " " + test + " " + test + " " + test)
# segments = []
# for i, s in enumerate(ss):
#     segment = {"start": i, "end":i, "text":s}
#     segments.append(segment)
# chunk_segments = chunk_text(segments)

# print("---POST")
# for seg in chunk_segments:
#     print(seg)
#     print(" --")

# test = "Hi, my name is John Hunter. I'm a Senior Product Marketing Specialist at TE Connectivity, working in the Data and Devices Division, and I look after antennas. I'm here today to talk to you about Wi-Fi 6E. So what is Wi-Fi 6E? Wi-Fi 6E is the first major expansion in the available Wi-Fi networks and frequency ranges in almost 20 years. So what is the difference between Wi-Fi 6 and Wi-Fi 6e? Wi-Fi 6 was the sixth standard of Wi-Fi. It was introduced in 2019, making use of the same 2.4 and 5.5 gigahertz ranges that had been available for around 10 years, but offered increased speeds and security protocols. Wi-Fi 6e is simply a frequency extension of the existing Wi-Fi 6 standard. It offers operations in the highest six gigahertz band, which is 5.925 to 7.125 gigahertz. So why change the available Wi-Fi spectrum? Over the last 10 to 20 years, the use of Wi-Fi has become far more prevalent. There are more users with more smart devices, accessing more applications, downloads, streaming services, et cetera, all at the same time. So the loads on both public and private Wi-Fi networks has increased significantly. What is the advantage of Wi-Fi 6E versus Wi-Fi 6? Wi-Fi 6E offers operations in the highest six gigahertz frequency band. Operations in a higher frequency band mean higher data rates, higher bandwidths, and available at faster speeds to users. This means that use cases that place heavy demands on Wi-Fi networks, such as streaming, such as augmented reality, downloads, et cetera, they can be made available to users in larger data packages and at faster speeds. This offers a much improved user experience. The increase in spectrum to add the six gigahertz band also means that more users can access a network simultaneously without causing overloads or dropouts to the network. So what are the available antenna solutions from TE Connectivity for Wi-Fi 6E? TE Connectivity has a very broad Wi-Fi 6E antenna offering. From embedded antennas, miniaturized board mount solutions, terminal mount antennas, all the way up to larger outdoor infrastructure MIMO antennas, we have a solution for all of these in the Wi-Fi 6E spectrum. If you'd like more information on our Wi-Fi 6E antennas, if you have any questions about designing an antenna into your solution, or you have questions about a custom design, please do get in touch and we'd be happy to discuss your requirements."
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
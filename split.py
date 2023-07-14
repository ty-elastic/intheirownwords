from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

sentence_model = SentenceTransformer('all-distilroberta-v1')

SENTENCE_WINDOW = 4
SIMILARITY_THRESHOLD = 0.3
SCENE_OVERLAP = 5

def find_scene(project, start, end):
    for scene in project['scenes']:
        start_overlap = 0
        if scene['start'] > SCENE_OVERLAP:
            start_overlap = SCENE_OVERLAP
        if start >= (scene['start']-start_overlap) and end > scene['start'] and end <= (scene['end']+SCENE_OVERLAP):
            return scene
    return None

def determine_cutpoint(project, segments, offset, speaker_dialog):
    sentences = []
    segments_to_copy = SENTENCE_WINDOW
    for i in range(SENTENCE_WINDOW):
        segment = segments[offset]
        scene = find_scene(project, segment['start'], segment['end'])
        sentences.append(segment['text'])
        offset = offset + 1
        if offset >= len(segments):
            break
        if scene != None and 'scene.frame_num' in speaker_dialog and scene['frame_num'] != speaker_dialog['scene.frame_num']:
            #print("SPLIT BY FRAME")
            segments_to_copy = i+1
            break
        elif segment['speaker_id'] != speaker_dialog['speaker.id']:
            #print("SPLIT BY SPEAKER")
            segments_to_copy = i+1
            break

    embeddings = sentence_model.encode(sentences)
    for end in range(len(sentences)-1, 0, -1):
        sim = util.cos_sim(embeddings[0], embeddings[end])
        # print(sentences[0], " ", sentences[end], sim)
        if sim > SIMILARITY_THRESHOLD:
            if (end+1) < segments_to_copy:
                #print("SPLIT BY THOUGHT")
                segments_to_copy = end+1
            break

    return segments_to_copy, segments_to_copy!=SENTENCE_WINDOW

def split(project, segments):
    dialog_by_speaker = []

    segment_offset = 0
    speaker_dialog = {'speaker.id':"", 'text_blocks':[], 'scene.frame_num':None}

    if len(segments) > 0:
        scene = find_scene(project, segments[0]['start'], segments[0]['end'])
        speaker_dialog = {'speaker.id':segments[0]['speaker_id'], 'text_blocks':[], 'scene.frame_num':scene['frame_num']}

    while(segment_offset < len(segments)):
        # print ("seg_offset" + str(segment_offset) + " len=" + str(len(segments)))
        segments_to_copy, cutpoint = determine_cutpoint(project, segments, segment_offset, speaker_dialog)
        # print ("segments_to_copy=" + str(segments_to_copy))
        for i in range(segments_to_copy):
            if segment_offset+i >= len(segments):
                break
            segment = segments[segment_offset+i]
            speaker_dialog['speaker.id'] = segment['speaker_id']
            speaker_dialog['text_blocks'].append(segment['text'].strip())
            if 'start' not in speaker_dialog:
                speaker_dialog['start'] = segment['start']
            speaker_dialog['end'] = segment['end']

        segment_offset += segments_to_copy

        if cutpoint == True:
            # print(cutpoint)
            # print(speaker_dialog)
            if 'start' in speaker_dialog:
                speaker_dialog['text'] = ' '.join(speaker_dialog['text_blocks'])
                del speaker_dialog['text_blocks']
                dialog_by_speaker.append(speaker_dialog)
            if segment_offset < len(segments):
                segment = segments[segment_offset]
                speaker_dialog = {'speaker.id':segment['speaker_id'], 'text_blocks':[]}
                scene = find_scene(project, segment['start'], segment['end'])
                if scene is not None:
                    speaker_dialog['scene.start'] = scene['start']
                    speaker_dialog['scene.end'] = scene['end']
                    if 'frame_text' in scene:
                        speaker_dialog['scene.frame_text'] = scene['frame_text']
                    speaker_dialog['scene.frame_url'] = scene['frame_url']        
                    speaker_dialog['scene.frame_num'] = scene['frame_num']  

                speaker_dialog['project_id'] = project['id']
                speaker_dialog['media_url'] = project['media_url']
                speaker_dialog['title'] = project['title']
                speaker_dialog['date'] = project['date'].strftime('%Y-%m-%d')
                speaker_dialog['kind'] = project['kind']
                speaker_dialog['origin'] = project['origin']
                
    project['clauses'] = dialog_by_speaker
    return dialog_by_speaker

# res = split_by_thought(result["segments"])
# print(res)



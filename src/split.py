import chunk_text

SCENE_OVERLAP = 3
ELSER_TOKEN_LIMIT = 512

def find_scene(project, start, end):
    for scene in project['scenes']:
        start_overlap = 0
        if scene['start'] > SCENE_OVERLAP:
            start_overlap = SCENE_OVERLAP
        if start >= (scene['start']-start_overlap) and end > scene['start'] and end <= (scene['end']+SCENE_OVERLAP):
            return scene
    return None

def start_clause(chunk, start_segment, project):
    clause = {'speaker.id':chunk['speaker_id'], 'scene.frame_num':None, 'start': start_segment['start'], 'end': start_segment['end']}
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

    clause['text'] = ''
    return clause

def split_chunk(chunk, clauses, project):
    # print("---PRE")
    # print(chunk['segments'])
    chunk_segments = chunk_text.chunking_text(chunk['segments'])
    # print("---POST")
    # print(chunk_segments)

    clause = None
    for chunk_segment in chunk_segments:
        clause = start_clause(chunk, chunk_segment, project)
        for text in chunk_segment['text']:
            if len(clause['text'])+len(text) >= ELSER_TOKEN_LIMIT:
                print("forcing segmentation")
                clauses.append(clause)
                clause = start_clause(chunk, chunk_segment, project)
                clause['text'] = text
            else:
                clause['text'] = clause['text'] + ' ' + text
                clause['end'] = chunk_segment['end']
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
    return clauses

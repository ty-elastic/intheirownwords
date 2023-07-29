import chunk_text

SCENE_OVERLAP = 5

def find_scene(project, start, end):
    for scene in project['scenes']:
        start_overlap = 0
        if scene['start'] > SCENE_OVERLAP:
            start_overlap = SCENE_OVERLAP
        if start >= (scene['start']-start_overlap) and end > scene['start'] and end <= (scene['end']+SCENE_OVERLAP):
            return scene
    return None

def init_clause(segment, scene, project):
    clause = {'speaker.id':segment['speaker_id'], 'scene.frame_num':None, 'start': segment['start']}
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
    return clause

def split(project, segments):
    clauses = []
    clause = None
    clause_text_blocks = []

    for i, segment in enumerate(segments):
        scene = find_scene(project, segment['start'], segment['end'])
        if clause is None:
            clause = init_clause(segment, scene, project)
        if (scene != None and scene['frame_num'] != clause['scene.frame_num']) or (segment['speaker_id'] != clause['speaker.id']):
            #print("SPLIT")
            thoughts = chunk_text.chunking_text(clause_text_blocks)
            clause_text_blocks = []
            for thought in thoughts:
                clause['text'] = ' '.join(thought)
                clauses.append(clause)
                clause = init_clause(segment, scene, project)
        clause_text_blocks.append(segment['text'].strip())
        clause['end'] = segment['end']
        
    project['clauses'] = clauses
    return clauses

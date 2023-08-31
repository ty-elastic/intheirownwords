import os 
import shutil
import uuid
import ffmpeg
import storage
from datetime import datetime
import slides
import stt
import split
import es_clauses
import time
import json
import tracemalloc

#local disk temp prj directory
PROJECT_DIR = "prj"

SAMPLE_RATE = 16000

def delete_project(project):
    shutil.rmtree( project['path'], ignore_errors=True)

def conform_audio(project):
    project['conformed_audio'] = project['path'] + "/" + project['id'] + ".wav"
    try:
        # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
        # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
        out, _ = (
            ffmpeg.input(project['input'], threads=0)
            .output(project['conformed_audio'], acodec="pcm_s16le", ac=1, ar=SAMPLE_RATE)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
        return project['conformed_audio']
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

def create_project(input, source_url, title, date, kind, origin, save_frames, persist_days):

    project_id = str(uuid.uuid4())
    prj_path = os.path.join(PROJECT_DIR, project_id)
    shutil.rmtree(prj_path, ignore_errors=True)
    os.makedirs(prj_path)

    path_file, extension = os.path.splitext(input)
    media_path = os.path.join(prj_path, project_id + extension)
    shutil.copyfile(input, media_path)

    project = {
        "id": project_id,
        "input": media_path,
        "title": title,
        "date": date,
        "path": prj_path,
        "kind": kind,
        "origin": origin,
        "source_url": source_url,
        "save_frames": save_frames,
        "persist_days": persist_days,
        "date_uploaded": datetime.now(),
        "scenes": []
    }
    print(f"creating={project}")

    project['media_url'] = storage.upload_project_file(project, None, media_path)
    return project


def process(input, source_url, title, date, kind, origin, save_frames, persist_days):

    tracemalloc.start()

    start_time = time.time()

    project = create_project(input, source_url, title, date, kind, origin, save_frames, persist_days)
    print ("conform_audio")
    conform_audio(project)

    print ("detect_slides")
    slides.detect_slides(project)

    print ("speech_to_text")
    segments = stt.speech_to_text(project)

    print ("split")
    split.split(project, segments)

    print ("add_clauses")
    es_clauses.add_clauses(project)

    end_time = time.time()
    print (f"duration={end_time - start_time}")
    
    delete_project(project)

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    for stat in top_stats[:10]:
        print(stat)

import os 
import shutil
import uuid
import storage
from datetime import datetime
import slides
import stt
import split
import es_clauses
import time
import tracemalloc

#local disk temp prj directory
PROJECT_DIR = "prj"

def delete_project(project):
    shutil.rmtree( project['path'], ignore_errors=True)

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
        "date_uploaded": datetime.utcnow(),
        "scenes": []
    }
    print(f"creating={project}")

    project['media_url'] = storage.upload_project_file(project, None, media_path)
    return project

def dump_mem():
    print("----- MEM DUMP")
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('traceback')
    for stat in top_stats[:5]:
        print("--BLOCK")
        print("%s memory blocks: %.1f KiB" % (stat.count, stat.size / 1024))
        for line in stat.traceback.format():
            print(line)

def process(input, source_url, title, date, kind, origin, save_frames, persist_days):

    #tracemalloc.start(25)

    start_time = time.time()

    project = create_project(input, source_url, title, date, kind, origin, save_frames, persist_days)

    print ("speech_to_text")
    segments = stt.speech_to_text(project)

    print ("detect_slides")
    slides.detect_slides(project)

    print ("split")
    split.split(project, segments)

    print ("add_clauses")
    es_clauses.add_clauses(project)

    end_time = time.time()
    print (f"duration={end_time - start_time}")
    
    delete_project(project)

    #dump_mem()

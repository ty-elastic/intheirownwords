import prj
import datetime
import threading
import queue
import uuid
from datetime import datetime, date
import shutil
import traceback
import os 

INGEST_DIR="ingest"

q = queue.Queue()
jobs = []

def enqueue(input, source_url, title, date, kind, origin, save_frames):
    project = {
        "id": uuid.uuid4(),
        "input": input,
        "title": title,
        "date": date,
        "kind": kind,
        "origin": origin,
        "source_url": source_url,
        "save_frames": save_frames,
        'status': 'queued',
        'started': datetime.now(),
        'duration': 0
    }
    q.put(project)
    jobs.append(project)

def process_loop():
    while True:
        project = q.get()
        job = [x for x in jobs if x['id'] == project['id']][0]
        print(project)
        job['status'] = 'processing'
        started = datetime.now()

        try:
            prj.process(project['input'], 
                        project['source_url'], 
                        project['title'], 
                        project['date'].strftime('%m/%d/%y'), 
                        project['kind'], 
                        project['origin'],
                        True,
                        project['save_frames'])
            job['status'] = 'complete'
            job['duration'] = datetime.now() - started
        except Exception as inst:
            job['status'] = 'error'
            traceback.print_exc()
        if os.path.exists(project['input']):
            os.remove(project['input'])
        q.task_done()
        
def start():
    t = threading.Thread(target=process_loop)
    t.daemon = True
    t.start()

def get_status():
    return jobs

# always start queue (even if it isn't used)
start()
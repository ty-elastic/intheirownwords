import prj
import datetime
import threading
import queue
import uuid
from datetime import datetime, date
import shutil
import traceback
import os 
from pytube import YouTube

INGEST_DIR="ingest"
PERSIST_DAYS_DEFAULT=30

q = queue.Queue()
jobs = []

def enqueue(source_url, title, date, kind, origin, save_frames, persist_days=PERSIST_DAYS_DEFAULT, youtube_url=None, input=None):
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
        'duration': 0,
        'persist_days': persist_days,
        'youtube_url': youtube_url
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
            if project['youtube_url'] is not None:
                yt = YouTube(project['youtube_url'])
                videos = yt.streams.filter(progressive=True, file_extension='mp4').desc()
                print(videos)
                project['input'] = videos.first().download(output_path=INGEST_DIR,skip_existing=False,filename=str(uuid.uuid4()) + ".mp4")
                print(project['input'])

            prj.process(project['input'], 
                        project['source_url'], 
                        project['title'], 
                        project['date'].strftime('%m/%d/%y'), 
                        project['kind'], 
                        project['origin'],
                        project['save_frames'],
                        project['persist_days'])
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
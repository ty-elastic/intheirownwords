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
import copy

INGEST_DIR="ingest"
PERSIST_DAYS_DEFAULT=60
YT_RETRIES=2

q = queue.Queue()
jobs = []

def enqueue(source_url, title, date, kind, origin, save_frames, persist_days=PERSIST_DAYS_DEFAULT, youtube_url=None, input=None):
    project = {
        "id": str(uuid.uuid4()),
        "input": input,
        "title": title,
        "date": date,
        "kind": kind,
        "origin": origin,
        "source_url": source_url,
        "save_frames": save_frames,
        'status': 'queued',
        'queued': datetime.now(),
        'duration': 0,
        'persist_days': persist_days,
        'youtube_url': youtube_url
    }
    q.put(project)
    jobs.append(project)

def download_from_youtube(project):
    # Perform bulk insertion
    for i in range(YT_RETRIES):
        try:
            yt = YouTube(project['youtube_url'])
            videos = yt.streams.filter(progressive=True, file_extension='mp4').desc()
            print(videos)
            project['input'] = videos.first().download(output_path=INGEST_DIR,skip_existing=False,filename=str(uuid.uuid4()) + ".mp4")
            print(project['input'])
            return
        except Exception as inst:
            traceback.print_exc()
    raise Exception("failed to download yt video")

def process_loop():
    while True:
        project = q.get()
        job = [x for x in jobs if x['id'] == project['id']][0]
        print(project)
        job['status'] = 'processing'
        started = datetime.now()

        try:
            if project['youtube_url'] is not None:
                download_from_youtube(project)

            prj.process(project['input'], 
                        project['source_url'], 
                        project['title'], 
                        project['date'], 
                        project['kind'], 
                        project['origin'],
                        project['save_frames'],
                        project['persist_days'])
            job['status'] = 'complete'      
        except Exception as inst:
            job['status'] = 'error'
            traceback.print_exc()
        job['duration'] = (datetime.now() - started).total_seconds
        if project['input'] is not None and os.path.exists(project['input']):
            os.remove(project['input'])
        q.task_done()
        
def start():
    print('start q')
    # t = threading.Thread(target=process_loop)
    # t.daemon = True
    # t.start()
    process_loop()

def get_status():
    status = []
    for job in jobs:
        stat = {}
        for key in job:
            stat[key] = job[key]
        status.append(stat)
    return status
# always start queue (even if it isn't used)
#start()


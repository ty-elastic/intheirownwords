import prj
import datetime
import threading
import queue
import uuid

q = queue.Queue()
jobs = []

def enqueue(input, source_url, title, date, kind, origin, enable_scenes):
    project = {
        "id": uuid.uuid4(),
        "input": input,
        "title": title,
        "date": date,
        "kind": kind,
        "origin": origin,
        "source_url": source_url,
        "enable_scenes": enable_scenes,
        'status': 'queued'
    }
    q.put(project)
    jobs.append(project)

def process_loop():
    while True:
        project = q.get()
        job = [x for x in jobs if x['id'] == project['id']][0]
        print(project)
        job['status'] = 'processing'
        prj.process(project['input'], 
                     project['source_url'], 
                     project['title'], 
                     project['date'].strftime('%m/%d/%y'), 
                     project['kind'], 
                     project['origin'],
                     True,
                     project['enable_scenes'])
        q.task_done()
        job['status'] = 'complete'
        
def start():
    for i in range(1):
        t = threading.Thread(target=process_loop)
        t.daemon = True
        t.start()

def get_status():
    return jobs

# always start queue (even if it isn't used)
start()
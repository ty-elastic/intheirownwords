from persistqueue import Queue
import prj
import datetime
import threading

q = Queue("queue")

def enqueue(input, source_url, title, date, kind, origin, enable_scenes):
    project = {
        "input": input,
        "title": title,
        "date": date,
        "kind": kind,
        "origin": origin,
        "source_url": source_url,
        "enable_scenes": enable_scenes
    }
    q.put(project)

def process_loop():
    while True:
        project = q.get()
        prj.process(project['input'], 
                     project['source_url'], 
                     project['title'], 
                     project['date'], 
                     project['kind'], 
                     project['origin'],
                     True,
                     project['enable_scenes'])
        q.task_done()

def start():
    for i in range(1):
        t = threading.Thread(target=process_loop)
        t.daemon = True
        t.start()

import job
from datetime import datetime
from tornado.web import RequestHandler
import tornado
import es_clauses
import json

def ingest(upload):
    print(input)
    job.enqueue(upload['source_url'], upload['title'], datetime.strptime(upload['date'], '%Y-%m-%d'),
                upload['kind'], upload['origin'], upload['save_frames'], youtube_url=upload['youtube_url'])
    print("done")

class ImportHandler(RequestHandler):
    def get(self):
        print(f"URL={self.request.uri}")
        data = tornado.escape.json_decode(self.request.body)
        print ("in post method")
        print(data)
        ingest(data)
        return

class SearchHandler(RequestHandler):
    def get(self):
        origin = self.get_argument('origin')
        query = self.get_argument('query')
        size = int(self.get_argument('size'))
        kind = self.get_argument('kind')

        self.set_header("Content-Type", 'application/json')
        res = es_clauses.find_clauses(origin, query, es_clauses.METHOD_HYBRID, speaker_id=None, kind=kind, size=size)
        r = json.dumps(res)
        self.write(r)

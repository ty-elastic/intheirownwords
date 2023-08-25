
import job
from datetime import datetime
import json
import http.server
import socketserver
from typing import Tuple
from http import HTTPStatus
from http.server import HTTPServer
import threading


API_PORT=8000

def ingest(upload):
    print(input)
    job.enqueue(upload['source_url'], upload['title'], datetime.strptime(upload['date'], '%Y-%m-%d'),
                upload['kind'], upload['origin'], upload['save_frames'], youtube_url=upload['youtube_url'])
    print("done")

class Handler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, request: bytes, client_address: Tuple[str, int], server: socketserver.BaseServer):
        super().__init__(request, client_address, server)

    @property
    def api_response(self):
        return json.dumps({"message": "Hello world"}).encode()

    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(self.api_response))

    def do_POST(self):
        if self.path == '/import/youtube':
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            print ("in post method")
            self.data_string = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(self.data_string)
            print(data)
            ingest(data)
            return

def process_loop():
    # Create an object of the above class
    my_server = HTTPServer(('', API_PORT), Handler)
    # Star the server
    print(f"Server started at {API_PORT}")
    my_server.serve_forever()

def start():
    print("start api")
    t = threading.Thread(target=process_loop)
    t.daemon = True
    t.start()

start()
# process_loop()

def dummy():
    return True
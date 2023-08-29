
import job
from datetime import datetime
import json
import http.server
import socketserver
from typing import Tuple
from http import HTTPStatus
from http.server import HTTPServer
import threading
import es_clauses
from tornado.web import RequestHandler
import tornado

class ImportHandler(RequestHandler):
    def get(self):
        print(f"URL={self.request.uri}")
        data = tornado.escape.json_decode(self.request.body)
        print ("in post method")
        print(data)
        ingest(data)
        return

API_PORT=8000

#def search(origin, query, method, speaker_id, kind, size):
    #clauses = es_clauses.find_clauses(origin, query, method, speaker_id=speaker, kind=kind, size=size)

    #for clause in clauses:
        # text = "#### " + "[" + clause['title'] + "](" + clause["source_url"] + ")"
        # st.markdown(text)
        # text = clause['date'].strftime('%Y-%m-%d')
        # st.markdown(text)

        # col1, col2, = st.columns(2)

        # with col1:
        #     answer = es_ml.ask_question(clause['text'], query)
        #     context_answer = None
        #     if answer is not None:

        #         # context_answer, i, sentences = es_ml.find_sentence_that_answers_question(clause['text'], query, answer)
        #         # if context_answer is not None:
        #         #     text = ui_helpers.highlight_sentence(sentences, i)
        #         #     st.markdown(text)
        #         # else:
        #         #     escaped = ui_helpers.escape_markdown(clause['text'])
        #         #     text = "### _\""
        #         #     text = text + ":orange[" + escaped + "]"
        #         #     text = text + "\"_"
        #         #     st.markdown(text)

        #         start, stop = es_ml.find_text_that_answers_question(clause['text'], answer)

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
        if self.path == '/search':
            print("hi")
        else:
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
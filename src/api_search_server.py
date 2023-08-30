
import json
import os
from tornado.web import RequestHandler
from mimetypes import guess_type
import fsspec
import es_clauses
from yaml.loader import SafeLoader
import yaml
import bcrypt
import streamlit_authenticator as stauth

SEARCH_USERNAME = "apikey"

class ValidateKey:
    def __init__(self):
        with open('auth/users.yaml') as file:
            self.config = yaml.load(file, Loader=SafeLoader)
        self.credentials = self.config['credentials']
        self.credentials['usernames'] = {key.lower(): value for key, value in self.credentials['usernames'].items()}
        print(self.credentials['usernames'])

    def check_apikey(self, user, apikey):
        return bcrypt.checkpw(apikey.encode(), 
            self.credentials['usernames'][user]['password'].encode())

keyValidator = ValidateKey()

class SearchHandler(RequestHandler):
    def get(self):

        apiKey = self.get_argument('x-api-key')
        if not keyValidator.check_apikey(SEARCH_USERNAME, apiKey):
            self.set_status(401)
            self.write("unauthorized")
            self.finish()
            return

        origin = self.get_argument('origin')
        query = self.get_argument('query')
        size=None
        if 'size' in self.request.arguments:
            size = self.get_argument('size')
        kind=None
        if 'kind' in self.request.arguments: 
            kind = self.get_argument('kind')

        self.set_header("Content-Type", 'application/json')
        res = es_clauses.find_clauses(origin, query, es_clauses.METHOD_HYBRID, speaker_id=None, kind=kind, size=size)
        print(res)
        r = json.dumps(res)
        self.write(r)

class StatusHandler(RequestHandler):
    def get(self):
        self.write("OK")

def get_file(remote_path):
    if os.getenv('AWS_S3_BUCKET') != None:
        fs = fsspec.filesystem('s3')
        return fs.open("s3://" + os.getenv('AWS_S3_BUCKET') + remote_path)
    elif os.getenv('GCP_GCS_BUCKET') != None:
        fs = fsspec.filesystem('gcs')
        print("gcs://" + os.getenv('GCP_GCS_BUCKET') + remote_path)
        return fs.open("gcs://" + os.getenv('GCP_GCS_BUCKET') + remote_path)

class MediaHandler(RequestHandler):
    def get(self):
        print(f"URL={self.request.uri}")
        content_type, _ = guess_type(self.request.uri)
        self.add_header('Content-Type', content_type)
        print(content_type)
        path = self.request.uri
        print(path)
        with get_file(path) as source_file:
            self.write(source_file.read())
        self.set_status(200)
        self.finish()
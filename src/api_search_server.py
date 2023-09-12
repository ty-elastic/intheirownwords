
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
import storage
import tornado
import es_origins
import requests

from api_import_client import API_PORT

SEARCH_USERNAME = "apikey"
IMPORT_PEERNAME = "ingest"

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

class OriginHandler(RequestHandler):
    # should be post, by streamlit has some global post handler
    def get(self):

        apiKey = self.get_argument('x-api-key')
        if not keyValidator.check_apikey(SEARCH_USERNAME, apiKey):
            self.set_status(401)
            self.write("unauthorized")
            self.finish()
            return

        data = tornado.escape.json_decode(self.request.body)
        print(data)

        origin_id = es_origins.hash_origin_id(data['origin'])

        response = requests.get(data['logo_url'], allow_redirects=True) 
        logo_url = storage.upload_logo(data['logo_url'], response.content, origin_id)

        es_origins.add_origin(origin_id, data['origin'], logo_url, data['homepage_url'], data['kinds'], data['results.size'])
        self.set_status(200)
        self.finish()

class ImportHandler(RequestHandler):
    # should be post, by streamlit has some global post handler
    def get(self):
        apiKey = self.get_argument('x-api-key')

        if not keyValidator.check_apikey(SEARCH_USERNAME, apiKey):
            self.set_status(401)
            self.write("unauthorized")
            self.finish()
            return

        data = tornado.escape.json_decode(self.request.body)
        print(data)
        response = requests.post(f"http://{IMPORT_PEERNAME}:{API_PORT}/import", json=data)
        print(response)
        self.set_status(response.status_code)
        self.finish()

class SearchHandler(RequestHandler):
    def get(self):

        print('searching')

        apiKey = self.get_argument('x-api-key')
        if not keyValidator.check_apikey(SEARCH_USERNAME, apiKey):
            self.set_status(401)
            self.write("unauthorized")
            self.finish()
            return
        print('here')
        
        origin = self.get_argument('origin')
        query = self.get_argument('query')
        size=None
        if 'size' in self.request.arguments:
            size = self.get_argument('size')
        kinds=None
        if 'kinds' in self.request.arguments: 
            kinds_args = self.request.arguments.get("kinds")
            kinds = []
            for arg in kinds_args:
                kinds.append(self.decode_argument(arg))
            print(kinds)

        self.set_header("Content-Type", 'application/json')
        res = es_clauses.find_clauses(origin, query, speaker_id=None, kinds=kinds, size=size)
        print(res)
        r = json.dumps(res)
        self.write(r)

class StatusHandler(RequestHandler):
    def get(self):
        self.write("OK")

class MediaHandler(RequestHandler):
    def get(self):
        print(f"URL={self.request.uri}")
        content_type, _ = guess_type(self.request.uri)
        self.add_header('Content-Type', content_type)
        print(content_type)
        path = self.request.uri
        print(path)
        with storage.get_file(path) as source_file:
            self.write(source_file.read())
        self.set_status(200)
        self.finish()
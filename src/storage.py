
import os
import fsspec
import shutil
import datetime

import datetime as dt
from google import auth
from google.cloud import storage
from google.oauth2 import service_account
from mimetypes import guess_type

ORIGIN_BUCKET = "origins"
PROJECT_BUCKET = "projects"

INGEST_DIR="ingest"
PROJECT_DIR = "prj"

FS = None
BUCKET_PATH = ""
BUCKET_NAME = ""
if os.getenv('AWS_S3_BUCKET'):
    FS = fsspec.filesystem('s3')
    BUCKET_PATH = "s3://" + os.getenv('AWS_S3_BUCKET')
    BUCKET_NAME = os.getenv('AWS_S3_BUCKET')
else:
    FS = fsspec.filesystem('gcs')
    BUCKET_PATH = "gcs://" + os.getenv('GCP_GCS_BUCKET')
    BUCKET_NAME = os.getenv('GCP_GCS_BUCKET')

def clean_temp_folders():
    clean_folder(INGEST_DIR)
    clean_folder(PROJECT_DIR)

def clean_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def upload_logo(file_name, file_buffer, origin_id):
    print(file_name)
    split_tup = file_name.split(".")
    split_tup.reverse()
    print("BLAH")
    print(split_tup)
    ext = "." + split_tup[0]
    print(ext)
    input = os.path.join(INGEST_DIR, origin_id + ext)
    with open(input, "wb") as f:
        f.write(file_buffer)

    file_path, file_name = os.path.split(input)
    remote_path = "/" + ORIGIN_BUCKET + "/" 
    remote_path += file_name
    logo_url = upload_file(input, remote_path)

    os.remove(input)
    print(logo_url)
    return logo_url

def delete_logo(logo_url):
    return FS.rm(BUCKET_PATH + logo_url)

def upload_file(local_path, remote_path):
    response = FS.put_file(local_path, BUCKET_PATH + remote_path)
    print(response)
    return remote_path

def delete_project(project_id):
    remote_path = "/" + PROJECT_BUCKET + "/" 
    remote_path = remote_path + project_id
    return FS.rm(BUCKET_PATH + remote_path, recursive=True)

def upload_project_file(project, remote_folder, local_path):
    file_path, file_name = os.path.split(local_path)
    remote_path = "/" + PROJECT_BUCKET + "/" 
    remote_path = remote_path + project['id'] + "/" 
    if remote_folder != None:
        remote_path += remote_folder + "/"
    remote_path += file_name
    return upload_file(local_path, remote_path)

def get_file(remote_path):
    print(BUCKET_PATH + remote_path)
    return FS.open(BUCKET_PATH + remote_path)

def setup_bucket_cors():
    if os.path.isfile('env/google_service_key.json'):
        credentials = service_account.Credentials.from_service_account_file(
            "env/google_service_key.json"
        )

        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(BUCKET_NAME)

        bucket.cors = [
            {
                "origin": ["*"],
                "responseHeader": [
                    "Content-Type",
                    "Access-Control-Allow-Origin",
                    "x-goog-resumable"
                ],
                "method": ["PUT", "GET", "HEAD", "DELETE", "POST", "OPTIONS"],
                "maxAgeSeconds": 3600
            }
        ]
        bucket.patch()
        print(f"Set CORS policies for bucket {bucket.name} is {bucket.cors}")
setup_bucket_cors()

def get_signed_url(blob_name):

    if os.path.isfile('env/google_service_key.json'):
        """Generates a v4 signed URL for uploading a blob using HTTP PUT.

        Note that this method requires a service account key file. You can not use
        this if you are using Application Default Credentials from Google Compute
        Engine or from the Google Cloud SDK.
        """
        # bucket_name = 'your-bucket-name'
        # blob_name = 'your-object-name'

        credentials = service_account.Credentials.from_service_account_file(
            "env/google_service_key.json"
        )

        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)

        content_type, _ = guess_type(blob_name)
        print(content_type)

        url = blob.generate_signed_url(
            version="v4",
            # This URL is valid for 24 hours
            expiration=datetime.timedelta(hours=24),
            # Allow PUT requests using this URL.
            method="GET",
            #content_type=content_type,
        )

        #print(url)
        return url

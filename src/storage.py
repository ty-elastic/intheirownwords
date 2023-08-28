
import os
import fsspec
from tornado.web import RequestHandler
from mimetypes import guess_type

ORIGIN_BUCKET = "origins"
PROJECT_BUCKET = "projects"

def upload_file(local_path, remote_path):
    if os.getenv('AWS_S3_BUCKET') != None:
        fs = fsspec.filesystem('s3')
        response = fs.put_file(local_path, "s3://" + os.getenv('AWS_S3_BUCKET') + remote_path)
        print(response)
        return remote_path
    elif os.getenv('GCP_GCS_BUCKET') != None:
        fs = fsspec.filesystem('gcs')
        response = fs.put_file(local_path, "gcs://" + os.getenv('GCP_GCS_BUCKET') + remote_path)
        print(response)
        return remote_path

def upload_project_file(project, remote_folder, local_path):
    file_path, file_name = os.path.split(local_path)
    remote_path = "/" + PROJECT_BUCKET + "/" 
    remote_path = project['id'] + "/" 
    if remote_folder != None:
        remote_path += remote_folder + "/"
    remote_path += file_name
    return upload_file(local_path, remote_path)

def upload_logo(local_path):
    file_path, file_name = os.path.split(local_path)
    remote_path = "/" + ORIGIN_BUCKET + "/" 
    remote_path += file_name
    return upload_file(local_path, remote_path)

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
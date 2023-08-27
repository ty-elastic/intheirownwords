
import os
import fsspec

ORIGIN_BUCKET = "origins"

def upload_file(local_path, remote_path):
    if os.getenv('AWS_S3_BUCKET') != None:
        fs = fsspec.filesystem('s3')
        response = fs.put_file(local_path, "s3://" + os.getenv('AWS_S3_BUCKET') + "/" + remote_path)
        print(response)
        return "https://" + os.getenv('AWS_S3_BUCKET') + ".s3.amazonaws.com/" + remote_path
    elif os.getenv('GCP_GCS_BUCKET') != None:
        fs = fsspec.filesystem('gcsfs')
        response = fs.put_file(local_path, "gcs://" + os.getenv('GCP_GCS_BUCKET') + "/" + remote_path)
        print(response)
        return "https://" + os.getenv('GCP_GCS_BUCKET') + ".s3.amazonaws.com/" + remote_path

def upload_project_file(project, remote_folder, local_path):
    file_path, file_name = os.path.split(local_path)
    remote_path = project['id'] + "/" 
    if remote_folder != None:
        remote_path += remote_folder + "/"
    remote_path += file_name
    upload_file(local_path, remote_path)

def upload_logo(local_path):
    file_path, file_name = os.path.split(local_path)
    remote_path = ORIGIN_BUCKET + "/" 
    remote_path += file_name
    upload_file(local_path, remote_path)
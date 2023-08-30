
import os
import fsspec

ORIGIN_BUCKET = "origins"
PROJECT_BUCKET = "projects"

INGEST_DIR="ingest"

def upload_logo(uploaded_file, origin_id):
    split_tup = os.path.splitext(uploaded_file.name)
    input = os.path.join(INGEST_DIR, origin_id + split_tup[1])
    with open(input, "wb") as f:
        f.write(uploaded_file.getbuffer())

    file_path, file_name = os.path.split(input)
    remote_path = "/" + ORIGIN_BUCKET + "/" 
    remote_path += file_name
    logo_url = upload_file(input, remote_path)

    os.remove(input)
    print(logo_url)
    return logo_url

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
    remote_path = remote_path + project['id'] + "/" 
    if remote_folder != None:
        remote_path += remote_folder + "/"
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

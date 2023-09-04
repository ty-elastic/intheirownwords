
import os
import fsspec
import shutil

ORIGIN_BUCKET = "origins"
PROJECT_BUCKET = "projects"

INGEST_DIR="ingest"
PROJECT_DIR = "prj"

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

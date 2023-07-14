import boto3
import os

def upload_file(project, remote_folder, local_path):
    if project['enable_write']:
        s3_client = boto3.client('s3')
        file_path, file_name = os.path.split(local_path)
        remote_path = project['id'] + "/" 
        if remote_folder != None:
            remote_path += remote_folder + "/"
        remote_path += file_name
        response = s3_client.upload_file(local_path, os.getenv('AWS_S3_BUCKET'), remote_path)
        #print(response)
        return "https://" + os.getenv('AWS_S3_BUCKET') + ".s3.amazonaws.com/" + remote_path

#upload_file({'id':'asldjasldjasldjalskd'}, '/hack/test/img/otel-Scene-001-01.jpg')
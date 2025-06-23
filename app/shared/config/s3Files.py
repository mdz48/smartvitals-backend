import time
import boto3
import os
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()

bucket_name = os.getenv('AWS_S3_BUCKET_NAME')

s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('aws_access_key_id'),
    aws_secret_access_key=os.getenv('aws_secret_access_key'),
    aws_session_token=os.getenv('aws_session_token'),
    region_name=os.getenv('aws_region', 'us-east-1'),
)

def upload_file_to_s3(file):
    file_key = f"{int(time.time())}_{file.filename}"
    
    try:
        s3.upload_fileobj(file.file, bucket_name, file_key, ExtraArgs={'ContentType': file.content_type})
        return f"https://{bucket_name}.s3.amazonaws.com/{file_key}"
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

def upload_files_to_s3(files):
    file_urls = []
    for file in files:
        file_key = f"{int(time.time())}_{file.filename}"
        try:
            s3.upload_fileobj(file.file, bucket_name, file_key, ExtraArgs={'ContentType': file.content_type})
            file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_key}"
            file_urls.append(file_url)
        except Exception as e:
            print(f"Error uploading file: {e}")
    return file_urls
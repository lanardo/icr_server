from __future__ import print_function
import boto3
import os
import uuid
from shutil import copyfile


s3_client = boto3.client('s3')


def copy_pdf(path, new_path):
    if os.path.exists(path):
        copyfile(path, new_path)


def handler(event, context):
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        download_path = '{}{}'.format(uuid.uuid4(), key)
        upload_path = 'copied-{}'.format(key)

        s3_client.download_file(bucket, key, download_path)
        copy_pdf(download_path, upload_path)
        s3_client.upload_file(upload_path, '{}copied'.format(bucket), key)

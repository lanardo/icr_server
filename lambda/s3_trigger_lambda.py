from __future__ import print_function
import boto3
import json
import requests


s3_client = boto3.client('s3')


def handler(event, context):
    record = event['Records'][0]

    src_bucket = record['s3']['bucket']['name']  # get source bucket name from the event
    path = record['s3']['object']['key']
    fname = path.split('/')[-1]

    print("src_bucket: ", src_bucket)
    print("file_path: ", path)
    print("file_name: ", fname)

    content = {"full_path": src_bucket + "/" + path}

    flask_server = "http://18.218.3.219:5000/api/trigger"
    r = requests.get(flask_server, json=content)


"""
{
  "Records": [
      {
          "s3" : {
              "bucket": {"name": "prod.pdf.ecofact.ai"},
              "object": {"key": "5b047ec345e74750135550fe/2018/May/Garant%20Bygg%20%26%20Bad%20AB/Credit/1527067362975-Testfaktura-312111.pdf"}
            }
      }
      ]
}
"""

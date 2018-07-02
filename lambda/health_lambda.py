from __future__ import print_function
import boto3


s3_client = boto3.client('s3')


def download_from_S3(bucket, s3_path, local_path):
    s3_client.download_file(bucket, s3_path, local_path)


def upload_to_S3(bucket, s3_path, local_path):
    s3_client.upload_file(local_path, bucket, s3_path)


def lambda_handler(event, context):
    record = event['Records'][0]

    src_bucket = record['s3']['bucket']['name']  # get source bucket name from the event
    path = record['s3']['object']['key']
    fname = path.split('/')[-1]

    print("src_bucket: ", src_bucket)
    print("file_path: ", path)
    print("file_name: ", fname)


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
import boto3

ACCESS_KEY = ""
SECRET_KEY = ""


s3_client = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)


def download_from_S3(bucket, s3_path, local_path):
    s3_client.download_file(bucket, s3_path, local_path)


def upload_to_S3(bucket, s3_path, local_path):
    s3_client.upload_file(local_path, bucket, s3_path)


if __name__ == '__main__':
    bucket = "prod.pdf.ecofact.ai"
    path = "5b047ec345e74750135550fe/2018/May/Garant Bygg & Bad AB/Credit/1527067362975-Testfaktura-312111.pdf"
    fname = "../data/" + path.split('/')[-1]
    download_from_S3(bucket=bucket, s3_path=path, local_path=fname)

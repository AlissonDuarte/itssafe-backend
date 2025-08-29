import os
import boto3
import json
from dotenv import load_dotenv


class AmazonS3Client:
    def __init__(self):
        load_dotenv()
        self.service='s3'
        self.aws_access_key_id=os.getenv('AWS_S3_ACCESS_KEY_ID')
        self.aws_secret_access_key=os.getenv('AWS_S3_SECRET_ACCESS_KEY')
        self.client=None

    def get_client(self):
        self.client = boto3.client(
            self.service,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        return self.client

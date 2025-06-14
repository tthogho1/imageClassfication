import boto3
import os
from dotenv import load_dotenv

load_dotenv()

sqs = boto3.client(
    "sqs",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

response = sqs.receive_message(
    QueueUrl="https://sqs.ap-northeast-1.amazonaws.com/584802445152/ImageFIle.fifo",
    AttributeNames=["All"],
)
print(response)

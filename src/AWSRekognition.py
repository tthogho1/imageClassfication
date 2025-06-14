import boto3
import logging
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore
import json

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()


def convertToJson(fileid, rekognition_outputs):
    """
    Convert an object to JSON format.
    """
    categories = []
    for item in rekognition_outputs:
        for cat in item["Categories"]:
            if cat["Name"] not in categories:
                categories.append(cat["Name"])

    # tagsのリストを作成
    tags = []
    for item in rekognition_outputs:
        tag = {"name": item["Name"], "confidence": item["Confidence"]}
        tags.append(tag)

    # 結合して出力
    output = {"image_id": fileid, "categories": categories, "tags": tags}
    return output


class RekognitionImage:
    def __init__(self, image, image_name, rekognition_client):
        self.image = image
        self.image_name = image_name
        self.rekognition_client = rekognition_client

    def detect_labels(self, max_labels=10, min_confidence=50):
        try:
            response = self.rekognition_client.detect_labels(
                Image=self.image,
                MaxLabels=max_labels,
                MinConfidence=min_confidence,
            )
            labels = response["Labels"]
            logger.info("Detected %s labels.", len(labels))
            return labels
        except Exception as e:
            logger.exception("Couldn't detect labels in %s.", self.image_name)
            raise


# クライアントの初期化
rekognition_client = boto3.client(
    "rekognition",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

# Firestore初期化
firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if not firebase_admin._apps:
    try:
        if not firebase_credentials_path or not os.path.exists(
            firebase_credentials_path
        ):
            abs_path = (
                os.path.abspath(firebase_credentials_path)
                if firebase_credentials_path
                else None
            )
            logger.error(f"Firebase credentials file not found: {abs_path}")
            raise FileNotFoundError(f"Firebase credentials file not found: {abs_path}")
        cred = credentials.Certificate(firebase_credentials_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"Firestore initialization failed: {e}")
        raise
db = firestore.client()

# SQS/S3クライアント初期化
sqs = boto3.client(
    "sqs",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

# SQSからメッセージ受信
while True:
    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=10
    )
    messages = response.get("Messages", [])
    if not messages:
        logger.info("No messages in SQS queue. Waiting...")
        continue

    message = messages[0]
    event = json.loads(message["Body"])

    # SQSメッセージを削除
    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"])

    bucket_name = event["detail"]["bucket"]["name"]
    object_key = event["detail"]["object"]["key"]
    if not bucket_name or not object_key:
        logger.error(f"S3 path or bucket not found in SQS message: {event}")
        sqs.delete_message(
            QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message["ReceiptHandle"]
        )
        continue

    # S3から画像ファイルをメモリ上に取得
    s3_object = s3.get_object(Bucket=bucket_name, Key=object_key)
    image_bytes = s3_object["Body"].read()

    image = {"Bytes": image_bytes}
    fileName = os.path.basename(object_key)

    rekognition_image = RekognitionImage(image, fileName, rekognition_client)
    labels = rekognition_image.detect_labels()
    result = convertToJson(fileName, labels)
    doc_ref = db.collection(os.getenv("FIRESTORE_COLLECTION")).document(fileName)
    doc_ref.set(result)
    logger.info("Rekognition results saved to Firestore for %s.", fileName)

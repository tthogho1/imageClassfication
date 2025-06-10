import boto3
import logging
from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, firestore

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
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
db = firestore.client()

fileName = "1215281253.jpg"  # 物体検出を行う画像ファイル名
# 例：ローカルの画像ファイルから物体検出
with open(fileName, "rb") as image_file:
    image_bytes = image_file.read()
    image = {"Bytes": image_bytes}
    rekognition_image = RekognitionImage(image, fileName, rekognition_client)
    labels = rekognition_image.detect_labels()
    # print(labels)
    result = convertToJson(fileName, labels)
    # resutltをFirestoreに保存する
    doc_ref = db.collection("rekognition_results").document(fileName)
    doc_ref.set(result)


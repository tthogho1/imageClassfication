import boto3
import logging
import os
from dotenv import load_dotenv

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()


transcribe = boto3.client(
    "transcribe",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)


transcribe.start_transcription_job(
    TranscriptionJobName="higuma",
    Media={"MediaFileUri": "s3://audio4input/9EWRu4sUTcE.mp4"},
    MediaFormat="mp4",
    LanguageCode="ja-JP",
    OutputBucketName="audio4output",
)

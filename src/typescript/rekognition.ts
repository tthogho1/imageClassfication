import { RekognitionClient, DetectLabelsCommand, Label } from '@aws-sdk/client-rekognition';
import {
  SQSClient,
  ReceiveMessageCommand,
  DeleteMessageCommand,
  Message,
} from '@aws-sdk/client-sqs';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { initializeApp, cert, getApps } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import * as dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';

dotenv.config();

// ログ設定
const logger = {
  info: (message: string, ...args: any[]) => console.log(`INFO: ${message}`, ...args),
  error: (message: string, ...args: any[]) => console.error(`ERROR: ${message}`, ...args),
  exception: (message: string, ...args: any[]) => console.error(`EXCEPTION: ${message}`, ...args),
};

interface RekognitionOutput {
  Name: string;
  Confidence: number;
  Categories?: Array<{ Name: string }>;
}

interface ConvertedJson {
  image_id: string;
  categories: string[];
  tags: Array<{ name: string; confidence: number }>;
}

interface S3Event {
  detail: {
    bucket: {
      name: string;
    };
    object: {
      key: string;
    };
  };
}

function convertToJson(fileid: string, rekognitionOutputs: Label[]): ConvertedJson {
  const categories: string[] = [];

  for (const item of rekognitionOutputs) {
    if (item.Categories) {
      for (const cat of item.Categories) {
        if (cat.Name && !categories.includes(cat.Name)) {
          categories.push(cat.Name);
        }
      }
    }
  }

  // tagsのリストを作成
  const tags = rekognitionOutputs.map(item => ({
    name: item.Name || '',
    confidence: item.Confidence || 0,
  }));

  // 結合して出力
  return {
    image_id: fileid,
    categories,
    tags,
  };
}

class RekognitionImage {
  private image: { Bytes: Uint8Array };
  private imageName: string;
  private rekognitionClient: RekognitionClient;

  constructor(
    image: { Bytes: Uint8Array },
    imageName: string,
    rekognitionClient: RekognitionClient
  ) {
    this.image = image;
    this.imageName = imageName;
    this.rekognitionClient = rekognitionClient;
  }

  async detectLabels(maxLabels: number = 10, minConfidence: number = 50): Promise<Label[]> {
    try {
      const command = new DetectLabelsCommand({
        Image: this.image,
        MaxLabels: maxLabels,
        MinConfidence: minConfidence,
      });

      const response = await this.rekognitionClient.send(command);
      const labels = response.Labels || [];
      logger.info(`Detected ${labels.length} labels.`);
      return labels;
    } catch (error) {
      logger.exception(`Couldn't detect labels in ${this.imageName}.`);
      throw error;
    }
  }
}

// クライアントの初期化
const rekognitionClient = new RekognitionClient({
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
  region: process.env.AWS_REGION,
});

// Firestore初期化
const firebaseCredentialsPath = process.env.FIREBASE_CREDENTIALS_PATH;
if (getApps().length === 0) {
  try {
    if (!firebaseCredentialsPath || !fs.existsSync(firebaseCredentialsPath)) {
      const absPath = firebaseCredentialsPath ? path.resolve(firebaseCredentialsPath) : null;
      logger.error(`Firebase credentials file not found: ${absPath}`);
      throw new Error(`Firebase credentials file not found: ${absPath}`);
    }

    const serviceAccount = JSON.parse(fs.readFileSync(firebaseCredentialsPath, 'utf8'));
    initializeApp({
      credential: cert(serviceAccount),
    });
  } catch (error) {
    logger.error(`Firestore initialization failed: ${error}`);
    throw error;
  }
}

const db = getFirestore();

// SQS/S3クライアント初期化
const sqs = new SQSClient({
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
  region: process.env.AWS_REGION,
});

const s3 = new S3Client({
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
  region: process.env.AWS_REGION,
});

const SQS_QUEUE_URL = process.env.SQS_QUEUE_URL!;

// メイン処理
async function main() {
  while (true) {
    try {
      const receiveCommand = new ReceiveMessageCommand({
        QueueUrl: SQS_QUEUE_URL,
        MaxNumberOfMessages: 1,
        WaitTimeSeconds: 10,
      });

      const response = await sqs.send(receiveCommand);
      const messages = response.Messages || [];

      if (messages.length === 0) {
        logger.info('No messages in SQS queue. Waiting...');
        continue;
      }

      const message = messages[0];
      const event: S3Event = JSON.parse(message.Body!);

      // SQSメッセージを削除
      await sqs.send(
        new DeleteMessageCommand({
          QueueUrl: SQS_QUEUE_URL,
          ReceiptHandle: message.ReceiptHandle,
        })
      );

      const bucketName = event.detail.bucket.name;
      const objectKey = event.detail.object.key;

      if (!bucketName || !objectKey) {
        logger.error(`S3 path or bucket not found in SQS message: ${JSON.stringify(event)}`);
        continue;
      }

      // S3から画像ファイルをメモリ上に取得
      const getObjectCommand = new GetObjectCommand({
        Bucket: bucketName,
        Key: objectKey,
      });

      const s3Object = await s3.send(getObjectCommand);
      const imageBytes = await s3Object.Body!.transformToByteArray();

      const image = { Bytes: imageBytes };
      const fileName = path.basename(objectKey);

      const rekognitionImage = new RekognitionImage(image, fileName, rekognitionClient);
      const labels = await rekognitionImage.detectLabels();
      const result = convertToJson(fileName, labels);

      const docRef = db.collection(process.env.FIRESTORE_COLLECTION!).doc(fileName);
      await docRef.set(result);

      logger.info(`Rekognition results saved to Firestore for ${fileName}.`);
    } catch (error) {
      logger.error(`Error processing message: ${error}`);
    }
  }
}

// 実行
console.log('Starting application...');
main().catch(console.error);

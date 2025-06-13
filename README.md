# AWSRekognition.py Usage Guide

## Overview

`AWSRekognition.py` is a Python script that performs object detection on images using AWS Rekognition and saves the results to Google Firestore.

## Prerequisites

- `requirements.txt`: List of required Python packages
- `.env`: Contains AWS credentials and the path to the Firebase credentials file
- `skywayproject-firebase-admin.json`: Firebase service account key file
- The image file for object detection (e.g., `1215281253.jpg`)

## Example .env

```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-northeast-1
FIREBASE_CREDENTIALS_PATH=skywayproject-firebase-admin.json
```

## How to Use

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
2. Prepare the `.env` file and the Firebase key file.
3. Set the image file name in `AWSRekognition.py`.
4. Run the script:
   ```powershell
   python src/AWSRekognition.py
   ```
5. The detection results will be saved in the `rekognition_results` collection in Firestore.

## Testing

Unit tests are available in `tests/test_AWSRekognition.py`.

```powershell
python -m unittest tests/test_AWSRekognition.py
```

## Notes

- AWS and Firebase credentials are required.
- If the Firebase key file is not found during initialization, an error with the full path will be shown.
- Docker execution is supported (see Dockerfile).

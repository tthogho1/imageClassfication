# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Create working directory
WORKDIR /app

# Copy dependency file
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and resources
COPY src/ ./src/
COPY tests/ ./tests/
COPY 1215281253.jpg ./
COPY skywayproject-firebase-admin.json ./
COPY .env ./

# Main script execution (change as needed)
CMD ["python", "src/AWSRekognition.py"]

from google.cloud import storage
import os

# CONFIG
BUCKET_NAME = "interview-practice-tool-storage"
LOCAL_FILE = "output/itv_daily_31032026.csv"

print(f"Uploading: {LOCAL_FILE}")

# Create client with explicit project
client = storage.Client(project="interview-practice-tool-491903")

# Get bucket
bucket = client.bucket(BUCKET_NAME)

# Upload file
blob = bucket.blob(os.path.basename(LOCAL_FILE))
blob.upload_from_filename(LOCAL_FILE)

print("Upload successful!")
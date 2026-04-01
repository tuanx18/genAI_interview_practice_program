from google.cloud import storage
import os
from datetime import datetime

today = datetime.now().strftime("%d%m%Y")

BASE_DIR = r"C:\Users\Admin\Desktop\Github Repos\genAI_interview_practice_program"

# CONFIG
BUCKET_NAME = "interview-practice-tool-storage"
LOCAL_FILE = os.path.join(
    BASE_DIR,
    "output",
    f"itv_daily_{today}.csv"
)

print(f"Uploading: {LOCAL_FILE}")

# Create client with explicit project
client = storage.Client(project="interview-practice-tool-491903")

# Get bucket
bucket = client.bucket(BUCKET_NAME)

# Upload file
blob = bucket.blob(os.path.basename(LOCAL_FILE))
blob.upload_from_filename(LOCAL_FILE)

print("Upload successful!")
import json
from google.cloud import storage

def fetch_latest_blob_from_gcs(bucket_name: str, prefix: str) -> str:
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    blobs = list(bucket.list_blobs(prefix=prefix))
    if not blobs:
        raise FileNotFoundError(f"No files found in GCS path with prefix: {prefix}")

    latest_blob = max(blobs, key=lambda b: b.updated)
    return latest_blob.name

def load_json_from_gcs(bucket_name, blob_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    return json.loads(blob.download_as_text())
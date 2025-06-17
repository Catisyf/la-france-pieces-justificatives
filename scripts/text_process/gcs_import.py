import logging
import json
from google.cloud import storage

# basic logging config
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def download_collection(prefix: str, bucket_name: str):
    client = storage.Client()

    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    poems = []
    for blob in blobs:
        content = blob.download_as_text()
        text = json.loads(content)
        poems.append(text)

    logger.info(f"Downloaded {len(poems)} poem(s) from GCS.")
    return poems

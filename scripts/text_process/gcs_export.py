import logging
import json
import datetime
from google.cloud import storage

# basic logging config
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def upload_poem(poem: dict, gcs_prefix: str, bucket_name: str):
    client = storage.Client()
    slug = poem["slug"]
    date = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"{gcs_prefix}{slug}_{date}.json"

    blob = client.bucket(bucket_name).blob(filename)
    blob.upload_from_string(
        json.dumps(poem, ensure_ascii=False, indent=2), content_type="application/json"
    )
    logger.info(f"Uploaded {filename} to GCS.")


def upload_collection(poems: list[dict], gcs_prefix: str, bucket_name: str):
    for poem in poems:
        upload_poem(poem, gcs_prefix, bucket_name)

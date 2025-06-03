import logging
import os
import json
import datetime
from google.cloud import storage

# basic logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def upload_output(output: dict, mode: str, gcs_prefix: str, bucket_name: str):

    """
    Uploads a dictionary as a JSON file to GCS.

    Args:
        output (dict): The JSON-serializable dictionary to upload.
        mode (str): Either 'llm' or 'emoji', used to determine storage path.

    Raises:
        ValueError: If mode is not one of the expected values.
    """

    client = storage.Client()
    date = datetime.datetime.now().strftime("%Y%m%d")
    if mode == "llm":
        filename = f"{gcs_prefix}llm_output_{date}.json"
    elif mode == "emoji":
        filename = f"{ gcs_prefix}emoji_output_{date}.json"
    else:
        raise ValueError(f"Invalid mode '{mode}'. Expected 'llm' or 'emoji'.")

    blob = client.bucket(bucket_name).blob(filename)
    blob.upload_from_string(
        json.dumps(output, ensure_ascii=False, indent=2),
        content_type="application/json"
    )
    logger.info(f"Uploaded {filename} to GCS.")
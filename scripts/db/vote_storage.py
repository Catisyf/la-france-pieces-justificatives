import logging
from google.cloud import firestore
from datetime import datetime, timezone

# basic logging config
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def store_vote(vote_list):
    db = firestore.Client()
    db.collection("votes").add(
        {"timestamp": datetime.now(timezone.utc), "votes": vote_list}
    )


logger.info("Successfully recorded user votes.")

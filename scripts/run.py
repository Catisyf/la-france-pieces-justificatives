import os
import sys
import logging
from dotenv import load_dotenv
from .text_process.gdocs_import import GDocsImporter
from .text_process.gcs_export import upload_collection
from .text_process.gcs_export_nlp import upload_output
from .text_process.gcs_import import download_collection
from .transformers.emoji_classifier_en import run_emoji_analysis
from .transformers.llm_interpreter import run_gpt_analysis

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

GOOGLE_DOCS_CREDS_PATH= os.getenv("GOOGLE_CREDS_PATH", "secrets/credentials.json")
GOOGLE_CLOUD_CREDS_PATH = os.getenv("GOOGLE_CLOUD_CREDS_PATH", "secrets/service_account.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_CREDS_PATH
SCOPES = os.getenv("GOOGLE_DOC_SCOPES", "").split(",")
DOC_ID = os.getenv("GOOGLE_DOC_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET")
# GCS folder 
GCS_PREFIX = "data/poems/"  
GCS_PREFIX_LLM = "data/llm/"  
GCS_PREFIX_EMOJI = "data/emoji/"

def validate_poem_parse(poems: list[dict]) -> None:
    invalid = []
    for poem in poems:
        title = poem.get("title")
        body = poem.get("body")
        date = poem.get("date")
        slug = poem.get("slug")
        
        if not title or not body or not date or not slug:
            body_snippet = body[:40].replace("\n", " ") + "…" if body else "<no body>"
            label = f"title: '{title or '<no title>'}', snippet: '{body_snippet}'"
            invalid.append(label)

    if invalid:
        raise ValueError(f"❌ Parse validation failed for poems: {invalid}")
    else:
        logger.info("✅ All poems passed validation.")

if __name__ == "__main__":
    try:
       #import poems from GDocs, parse and validate
        logger.info("📄 Starting GDocs import...")

        importer = GDocsImporter(
            creds_path=GOOGLE_DOCS_CREDS_PATH,
            scopes=SCOPES,
            doc_id=DOC_ID
        )

        documents = importer.fetch_google_doc(DOC_ID)
        poems = importer.parse_google_doc(documents)
        validate_poem_parse(poems)

        #store poems in GCS bucket
        logger.info(f"✅ Parsed {len(poems)} poems. Uploading to GCS...")
        upload_collection(poems, GCS_PREFIX, BUCKET_NAME)
        logger.info("🎉 Done! Poems uploaded.")

        #download poems from GCS bucket
        collection = download_collection(GCS_PREFIX, BUCKET_NAME)
        logger.info("🎉 Done! Poems downloaded.")

        if collection: 
            #emoji analys over English poems
            emoji_output = run_emoji_analysis(collection)
            upload_output(emoji_output, "emoji", GCS_PREFIX_EMOJI, BUCKET_NAME)
            logger.info("🚀 All processing complete. Emoji outputs saved to GCS.")

            #gpt related anaysis
            llm_output = run_gpt_analysis(collection)
            upload_output(llm_output, "llm", GCS_PREFIX_LLM, BUCKET_NAME)
            logger.info("🚀 All processing complete. llm outputs saved to GCS.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1) 


import logging
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import unicodedata
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import re

# basic logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class GDocsImporter:
    def __init__(self, creds_path, scopes, doc_id):
        self.creds_path = creds_path
        self.scopes = scopes
        self.doc_id = doc_id
        self.service = self._auth()

    def _auth(self):
        """Authenticate and return Google Docs API service."""
        flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, self.scopes)
        creds = flow.run_local_server(port=0)
        return build("docs", "v1", credentials=creds)

    def _normalize_title(self, title: str) -> str:
        title_str = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("utf-8")
        title_str = title_str.lower().strip()
        title_str = title_str.replace("°", "no").replace(" ", "_")
        return title_str

    def fetch_google_doc(self, doc_id: str):
        """Download the Google Doc content."""
        return self.service.documents().get(documentId=doc_id).execute()

    def parse_google_doc(self, document: dict) -> list[dict]: 
        content = document.get("body", {}).get("content", [])
        poems = []
        current_poem = {}
        body_lines = []
        expecting_date = False
        collecting_body = False
        for element in content:
            paragraph = element.get("paragraph")
            if not paragraph:
                continue
            style = paragraph.get("paragraphStyle", {}).get("namedStyleType")
            text_chunks = [
                run.get("textRun", {}).get("content", "").strip()
                for run in paragraph.get("elements", [])
                if run.get("textRun")
            ]
            full_line = " ".join(text_chunks).strip()
            if not full_line:
                continue
            # 🟢 Poem title
            if style == "HEADING_4":
                # Finalize previous poem
                if current_poem and body_lines:
                    raw_body = " ".join(body_lines)
                    clean_body = re.sub(r"[\s\x0b]+", " ", raw_body).strip()
                    current_poem["body"] = clean_body
                    try:
                        current_poem["language"] = detect(clean_body)
                    except LangDetectException:
                        current_poem["language"] = "unknown"
                    poems.append(current_poem)
                    body_lines = []
                current_poem = {
                    "title": full_line,
                    "slug": self._normalize_title(full_line)
                }
                expecting_date = True
                collecting_body = False
                continue
            # 📆 Date + optional first line
            if expecting_date and style == "NORMAL_TEXT":
                tokens = full_line.strip().split(" ", 1)
                date_str = tokens[0]
                poem_start = tokens[1] if len(tokens) > 1 else ""
                current_poem["date"] = date_str
                expecting_date = False
                collecting_body = True
                if poem_start:
                    body_lines.append(poem_start)
                continue
            # 📝 Poem body
            if collecting_body and style == "NORMAL_TEXT":
                body_lines.append(full_line.strip())
        # Final poem
        if current_poem and body_lines:
            raw_body = " ".join(body_lines)
            clean_body = re.sub(r"[\s\x0b]+", " ", raw_body).strip()
            current_poem["body"] = clean_body
            try:
                current_poem["language"] = detect(clean_body)
            except LangDetectException:
                current_poem["language"] = "unknown"
            poems.append(current_poem)
        
        logger.info(f"{len(poems)} poems parsed.")
        logger.info(f"{poems[0]} poems parsed.")

        return poems
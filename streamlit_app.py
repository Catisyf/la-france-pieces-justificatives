import os
import streamlit as st
import openai
import re
from dotenv import load_dotenv
from scripts.text_process.gcs_import import download_collection
from scripts.text_process.gcs_import_nlp import load_json_from_gcs, fetch_latest_blob_from_gcs

# === Setup ===
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_CLOUD_CREDS_PATH")
BUCKET_NAME = os.getenv("GCS_BUCKET")
GCS_PREFIX = "data/poems/"
openai.api_key = os.getenv("OPENAI_API_KEY")

THEME_EMOJIS = {
    "Existential Conundrums": "🌀",
    "Work-Life Balance and Professional Challenges": "💼",
    "Coping with Reality": "🧠",
    "Life and Death": "🪦"
}

LOW_CONFIDENCE_EMOJIS = {
    "document_egare_n2",
}

st.set_page_config(page_title="Poetic Interpreter", layout="wide")

# === CSS: Shrink font sizes and fix layout ===
st.markdown("""
<style>
h1 {
    font-size: 28px !important;
    font-weight: 700 !important;
    color: #1a1a1a;
    margin-bottom: 0.5rem !important;
}

h2 {
    font-size: 24px !important;
    font-weight: 650 !important;
    color: #2c2c2c;
    margin-top: 1rem !important;
    margin-bottom: 0.4rem !important;
}

h3, h4 {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: #333;
    margin-bottom: 0.4rem !important;
}

p, li {
    font-size: 17px !important;
    line-height: 1.65 !important;
    color: #333;
}

.card-box {
    background-color: #fff;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1.5rem;
    min-height: 200px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
    border: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# === Load data ===
@st.cache_data
def load_latest_outputs():
    llm_path = fetch_latest_blob_from_gcs(BUCKET_NAME, "data/llm/")
    emoji_path = fetch_latest_blob_from_gcs(BUCKET_NAME, "data/emoji/")
    return (
        load_json_from_gcs(BUCKET_NAME, llm_path),
        load_json_from_gcs(BUCKET_NAME, emoji_path),
        llm_path
    )

@st.cache_data
def get_poems():
    return download_collection(GCS_PREFIX, BUCKET_NAME)

llm_output, emoji_output, llm_path = load_latest_outputs()
poems = get_poems()

# === Header ===
st.markdown("# 📖 Poetry Decoded")
st.caption(f"LLM output: `{llm_path.split('/')[-1]}`")

# === Thematic Groupings ===
st.markdown("## 📚 Thematic Groupings")
st.markdown("_Generated using `OpenAI's GPT-4` model_")

def extract_markdown_categories(raw):
    pattern = r"\*\*Category \d+: (.*?)\*\*\n(.*?)(?=\n\*\*Category \d+:|$)"
    matches = re.findall(pattern, raw, re.DOTALL)
    return [{"title": m[0].strip(), "description": m[1].strip()} for m in matches]

if llm_output and "categories" in llm_output:
    raw = llm_output["categories"]
    themes = extract_markdown_categories(raw)

    rows = [themes[i:i+2] for i in range(0, len(themes), 2)]
    for row in rows:
        cols = st.columns(2)
        for col, theme in zip(cols, row):
            emoji = THEME_EMOJIS.get(theme["title"], "🧩")
            col.markdown(f"<div class='card-box'><h4>{emoji} {theme['title']}</h4><p>{theme['description']}</p></div>", unsafe_allow_html=True)

# === GPT's Favorite Poems ===
st.markdown("## 🏆 GPT's Favorite Poems")
st.markdown("_Selected using `OpenAI's GPT-4` model_")

favorites = llm_output.get("favorites", "")
lines = [l.strip() for l in favorites.split("\n") if l.strip()]
emoji_map = {1: "🥇", 2: "🥈", 3: "🥉"}

for i, line in enumerate(lines[:3]):
    match = re.match(r"\d+\.\s*(.+?):\s*(.+)", line)
    if match:
        title, desc = match.groups()
        st.markdown(f"{emoji_map[i+1]} **{title}**  \n{desc}")

# === Emoji Reactions ===
st.markdown("## 🎭 Emoji Reactions")
st.markdown("_Predicted using `joeddav/distilbert-base-uncased-go-emotions-student` model_")

for poem in poems:
    if poem.get("language") == "en":
        slug = poem["slug"]
        title = poem["title"]
        emoji = emoji_output.get(slug, {}).get("emoji", "❓")

        if slug in LOW_CONFIDENCE_EMOJIS:
            st.markdown(f"- **{title}** — {emoji} ⚠️ _low confidence_")
        else:
            st.markdown(f"- **{title}** — {emoji}")

# === Poll ===
st.markdown("## 🗳️ Cast Your Vote")

title_lookup = {p['title']: p['slug'] for p in poems}
selected = st.multiselect(
    "Pick up to **three** poems you connected with most",
    options=list(title_lookup.keys()),
    max_selections=3,
    placeholder="Select up to 3..."
)

if selected:
    st.success("Thanks for voting!")
    for title in selected:
        st.markdown(f"- **{title}**")
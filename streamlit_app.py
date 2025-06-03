import os
import streamlit as st
import openai
import re
from dotenv import load_dotenv
from scripts.text_process.gcs_import import download_collection
from scripts.text_process.gcs_import_nlp import load_json_from_gcs, fetch_latest_blob_from_gcs

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_CLOUD_CREDS_PATH")
BUCKET_NAME = os.getenv("GCS_BUCKET")
GCS_PREFIX = "data/poems/"
openai.api_key = os.getenv("OPENAI_API_KEY")

THEME_EMOJIS = {
    "Existential Conundrums": "🌀",
    "Work-Life Balance and Professional Challenges": "💼",
    "Coping with Reality": "🧠",
    "Life and Death": "🌸"
}

# UI config
st.set_page_config(page_title="Poetic Interpreter", layout="wide")

# 💅 Inject CSS styling
st.markdown("""
<style>
body, html, .stApp {
    font-family: 'EB Garamond', serif;
    font-size: 18px;
    line-height: 1.6;
    color: #222;
    background-color: #faf9f7;
}
.card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
pre {
    background-color: #f3f3f3;
    padding: 1rem;
    border-radius: 8px;
    white-space: pre-wrap;
    font-family: 'EB Garamond', serif;
    font-size: 17px;
    line-height: 1.7;
}
.subtext {
    font-style: italic;
    color: #444;
    margin-top: 0.5rem;
}
</style>
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# 🧐 Load data
@st.cache_data
def load_latest_outputs():
    llm_path = fetch_latest_blob_from_gcs(BUCKET_NAME, "data/llm/")
    emoji_path = fetch_latest_blob_from_gcs(BUCKET_NAME, "data/emoji/")
    return (
        load_json_from_gcs(BUCKET_NAME, llm_path),
        load_json_from_gcs(BUCKET_NAME, emoji_path),
        llm_path
    )

llm_output, emoji_output, llm_path = load_latest_outputs()

@st.cache_data
def get_poems():
    return download_collection(GCS_PREFIX, BUCKET_NAME)

poems = get_poems()

# 🌟 Header
st.title("📖 Poetic Interpreter")
st.caption(f"LLM output: `{llm_path.split('/')[-1]}`")

# 🔂 Thematic Groupings (2x2 card layout)
st.header("📚 Thematic Groupings")

def extract_markdown_categories(raw):
    pattern = r"\*\*Category \d+: (.*?)\*\*\n(.*?)(?=\n\*\*Category \d+:|$)"
    matches = re.findall(pattern, raw, re.DOTALL)
    return [{"title": m[0].strip(), "description": m[1].strip()} for m in matches]

if llm_output and "categories" in llm_output:
    raw_categories = llm_output["categories"]
    themes = extract_markdown_categories(raw_categories)

    rows = [themes[i:i+2] for i in range(0, len(themes), 2)]
    for row in rows:
        cols = st.columns(2)
        for col, theme in zip(cols, row):
            emoji = THEME_EMOJIS.get(theme["title"], "🧩")
            col.markdown(f"""
            <div style='
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 16px;
                padding: 1.2rem;
                margin-bottom: 1.5rem;
                min-height: 220px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            '>
                <h4 style='margin-bottom: 0.5rem;'>{emoji} {theme['title']}</h4>
                <p style='font-size: 0.92rem;'>{theme['description']}</p>
            </div>
            """, unsafe_allow_html=True)

# 🏆 GPT's Favorite Poems
    st.header("🏆 GPT's Favorite Poems")

    favorites_block = llm_output.get("favorites", "")
    favorite_lines = [line.strip() for line in favorites_block.split('\n') if line.strip()]

    emoji_map = {
        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    for i, line in enumerate(favorite_lines[:3]):
        match = re.match(r"\d+\.\s*(.+?):\s*(.+)", line)
        if match:
            title, description = match.groups()
            st.markdown(f"{emoji_map[i+1]} **{title}**  \n{description}")

# 🎭 Emoji reactions
st.header("🎭 Emoji Reactions")
for poem in poems:
    if poem.get("language") == "en":
        emoji = emoji_output.get(poem["slug"], {}).get("emoji", "❓")
        st.markdown(f"**{poem['title']}** — {emoji}")

# 💖 Reader interaction
st.header("🗳️ Cast Your Vote")
st.markdown("Pick up to **three** poems you connected with most:")

title_lookup = {p['title']: p['slug'] for p in poems}
selected_titles = st.multiselect(
    "Your Top 3 Poems",
    options=list(title_lookup.keys()),
    max_selections=3,
    placeholder="Select up to 3..."
)

if selected_titles:
    st.markdown("### ✅ Thanks for voting!")
    st.write("You selected:")
    for title in selected_titles:
        st.markdown(f"- **{title}**")

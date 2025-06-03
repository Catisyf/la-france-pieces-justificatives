import os
from transformers import pipeline
from collections import defaultdict

EMOJI_MAP = {
    "remorse": "😔",          # quiet regret
    "grief": "💔",            # heartbreak
    "nervousness": "😬",      # unease, social dread
    "love": "❤️",             # deep feeling, warmth
    "excitement": "🤩",       # rush of energy
    "desire": "🔥",           # craving, passion
    "anger": "😠",            # heat, conflict
    "disappointment": "😞",   # sinking feeling
    "disapproval": "🙅",      # moral rejection
    "annoyance": "😒",        # minor frustration
    "confusion": "🤔",        # fog, uncertainty
    "caring": "🤗",           # soft empathy
    "embarrassment": "😳"     # vulnerability
}

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load the emotion classification pipeline
emotion_classifier = pipeline(
    "text-classification",
    model="joeddav/distilbert-base-uncased-go-emotions-student",
    return_all_scores=True,
    top_k=None
)

# Process results
def generate_score(poems):
    return [
        {
            "title": poem.get("title"),
            "slug": poem.get("slug"),
            "text": body,
            "label": result["label"],
            "score": round(result["score"], 4)
        }
        for poem in poems if poem.get("language") == "en"
        for body in [poem.get("body", "")]
        for result in emotion_classifier(body)[0]
    ]


def get_top_emotions_grouped(scores, top_k=3):
    grouped = defaultdict(list)

    # Step 1: Group all scores by slug
    for entry in scores:
        grouped[entry["slug"]].append({
            "text": entry["text"],
            "label": entry["label"],
            "score": round(entry["score"], 4)
        })

    # Step 2: Sort each group and keep top K
    top_emotions = {
        slug: sorted(emotions, key=lambda x: x["score"], reverse=True)[:top_k]
        for slug, emotions in grouped.items()
    }

    return top_emotions

# Map emojis
def enrich_with_emoji(dominant_emotions, emoji_map):
    enriched_emojis = {}

    for slug, emotions in dominant_emotions.items():
        if not emotions:
            continue  # Skip if no emotion scores available

        dominant = max(emotions, key=lambda x: x["score"])
        emoji = emoji_map.get(dominant["label"], "")

        enriched_emojis[slug] = {
            "top_emotions": emotions,
            "emoji": emoji
        }

    return enriched_emojis

# Run 
def run_emoji_analysis(poems):
    scores = generate_score(poems)
    dominant_emotions= get_top_emotions_grouped(scores, top_k=3)
    return enrich_with_emoji(dominant_emotions, EMOJI_MAP)

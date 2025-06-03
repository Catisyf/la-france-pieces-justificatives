import openai
import os
import logging

# basic logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Format all poems into a readable string
def format_poem_collection(poems):
    return "\n\n".join(
        f"---\n{p['slug']}\n{p['title']}\n{p['body'].strip()}"
        for p in poems
    )

# GPT prompt
def ask_gpt(prompt: str, model: str = "gpt-4", max_tokens: int = 1500, temperature: float = 0.7) -> str:
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a thoughtful literary critic."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.info(f"[GPT Error]: {e}")
        return f"[Error]: {str(e)}"
    

# Run 
def run_gpt_analysis(poems):
    formatted = format_poem_collection(poems)

    logger.info("\n🔍 Grouping poems by theme...")
    grouping_prompt = f""" 
    I'll give you a collection of short poems. 
    Group them into 3-4 thematic categories based on tone and subtext. 
    Name each category and describe what connects them.

    Poems:
    {formatted}
    """
    categories = ask_gpt(grouping_prompt)

    logger.info("\n👀 Reading subtexts...")
    subtext_prompt = f"""You're a poet's inner voice. 
    For each poem, write one sentence that captures what the poet felt but didn't say out loud.

    Poems:
    {formatted}
    """
    subtexts = ask_gpt(subtext_prompt)

    logger.info("\n🥇 Picking my favorites...")
    favorites_prompt = f"""Read all short poems below and pick your top 3 favorites. 
    Rank them 1 to 3 and explain why you chose each one.

    Poems:
    {formatted}
    """
    favorites = ask_gpt(favorites_prompt)

    return {
        "categories": categories,
        "subtexts": subtexts,
        "favorites": favorites
    }

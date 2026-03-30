import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def generate_linkedin_post(articles: list, instruction: str) -> list:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set. Please update your .env file.")
        
    client = genai.Client(api_key=api_key)
    
    articles_context = "Recent News Articles:\n\n"
    for idx, article in enumerate(articles[:30]): 
        articles_context += f"{idx+1}. {article['title']}\n"
        articles_context += f"Source: {article['source']}\n"
        articles_context += f"Summary: {article['summary'][:300]}...\n"
        articles_context += f"Link: {article['link']}\n\n"
        
    system_persona = """Act as a pragmatic, highly experienced Senior Backend Developer who is skeptical of pure hype. \
You care about system architecture, real-world trade-offs, local AI implementation, and actual developer experience. \
Your tone is conversational, sharp, and slightly contrarian. Do not sound like a marketer."""

    prompt = f"""
    {system_persona}

    Additional context from the operator:
    {instruction}

    Step 1: Analyze and RANK the provided news stories based on what is most critical, trending, and impactful for the tech ecosystem.

    Step 2: From the top-ranked stories, draft exactly 3 DIFFERENT LinkedIn post options.
       - Option 1: A brief observation on one critical technical breakthrough.
       - Option 2: Connecting a trending news item to a real-world engineering problem.
       - Option 3: A punchy, slightly contrarian view on a hyped topic.

    Formatting Rules for EACH Post Option:
    - CRITICAL LENGTH CONSTRAINT: Each post MUST be extremely short. Exactly 3 to 4 lines maximum of actual text. Let the linked article do the heavy lifting.
    - CRITICAL STRUCTURE: 
        Part 1 (The Hook): What happened or the core architectural problem. (1 sentence)
        Part 2 (The Reflection): A natural, humane perspective. Start it conversationally, like "I've been thinking about this..." or "Looking at this, my first thought is..." (Do NOT use the phrase "Hot Take"). Focus on the trade-offs or scalability realities. (1-2 sentences)
        Part 3 (The Handoff): "Read the full breakdown:" followed by the source link.
    - Hit 'Enter' twice between every single thought to create maximum white space.
    - Keep the text crisp and highly engaging, ban corporate speak and marketing fluff.
    - Limit emojis to a maximum of 1 per post. Rely on strong vocabulary instead.
    - Do NOT use ANY markdown formatting symbols whatsoever (No asterisks, no underscores). Use plain text only.
    - Add 2-3 relevant hashtags at the bottom.

    FORMATTING YOUR FINAL OUTPUT:
    You MUST separate each of the 3 post options using exactly this delimiter on its own line:
    ===POST_SEPARATOR===
    Do not add conversational filler like "Here are the options:". Begin immediately with the first post option text.

    {articles_context}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    drafts = [draft.strip() for draft in response.text.split("===POST_SEPARATOR===") if draft.strip()]
    return drafts

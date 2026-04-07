import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from db import fetch_recent_posts

load_dotenv()

def _build_history_context(recent_posts: list) -> str:
    """Build a context block from recent posts so the model avoids repetition."""
    if not recent_posts:
        return ""
    
    context = "\n\nPREVIOUSLY PUBLISHED POSTS (DO NOT repeat these topics, angles, or opening structures):\n"
    for i, post in enumerate(recent_posts, 1):
        # Truncate to first 200 chars to save tokens
        snippet = post.get("content", "")[:200]
        group = post.get("group_name", "")
        context += f"\n--- Post {i} ({group}) ---\n{snippet}...\n"
    return context

def _filter_already_covered(articles: list, recent_posts: list) -> list:
    """Remove articles whose titles are too similar to recently published content."""
    if not recent_posts:
        return articles
    
    recent_text = " ".join([p.get("content", "").lower() for p in recent_posts])
    recent_words = set(recent_text.split())
    
    filtered = []
    for article in articles:
        title_words = set(article["title"].lower().split())
        # If more than 60% of the title words appear in recent posts, skip it
        if len(title_words) > 2:
            overlap = len(title_words & recent_words) / len(title_words)
            if overlap > 0.6:
                continue
        filtered.append(article)
    
    # If filtering removed everything, return originals (better than nothing)
    return filtered if filtered else articles

def generate_linkedin_post(articles: list, instruction: str) -> list:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set. Please update your .env file.")
        
    client = genai.Client(api_key=api_key)
    
    # Fetch recent posts for history-aware generation
    recent_posts = fetch_recent_posts(limit=5)
    
    # Filter out articles already covered
    articles = _filter_already_covered(articles, recent_posts)
    
    articles_context = "Recent News Articles:\n\n"
    for idx, article in enumerate(articles[:30]): 
        articles_context += f"{idx+1}. {article['title']}\n"
        articles_context += f"Source: {article['source']}\n"
        articles_context += f"Summary: {article['summary'][:300]}...\n"
        articles_context += f"Link: {article['link']}\n\n"
    
    # Build history context
    history_context = _build_history_context(recent_posts)
        
    system_persona = """You are a real person — a senior engineer with 10+ years shipping production systems. \
You write like you talk: direct, a little dry, occasionally funny. You never sound like an AI or a LinkedIn influencer. \
You have genuine opinions shaped by painful production incidents and late-night debugging sessions. \
You're allergic to buzzwords, hype cycles, and anyone who says "game-changer" unironically."""

    prompt = f"""
    {system_persona}

    Additional context from the operator:
    {instruction}
    {history_context}

    Step 1: Analyze and RANK the provided news stories based on what is most critical, trending, and impactful for the tech ecosystem.

    Step 2: From the top-ranked stories, draft exactly 3 DIFFERENT LinkedIn post options.
       - Option 1: A brief observation on one critical technical breakthrough.
       - Option 2: Connecting a trending news item to a real-world engineering problem.
       - Option 3: A punchy, slightly contrarian view on a hyped topic.

    VOICE RULES (NON-NEGOTIABLE):
    - BANNED PHRASES: Never use any of these or similar filler: "I think", "I thought", "I've been thinking", "Looking at this", "my first thought is", "Here's the thing", "Let that sink in", "buckle up", "not gonna lie", "hot take". These are dead giveaways of AI-generated content.
    - EACH post must open DIFFERENTLY. Vary your sentence structures — start with a fact, a question, a short declarative statement, a number, or a direct opinion. Never start two posts the same way.
    - Write like you're texting a smart friend who works in tech, not like you're performing for an audience.
    - Use specific technical details when possible — name the architecture pattern, the framework, the metric. Vague commentary is boring.
    - It's okay to be uncertain. Real humans say "not sure this matters yet" or "jury's still out" — that reads more honestly than confident proclamations.

    STRUCTURE for EACH Post Option:
    - CRITICAL LENGTH: 3 to 4 lines of actual text MAX. Let the linked article do the heavy lifting.
    - Line 1 (The Hook): What happened, stated bluntly. One sentence. No fanfare.
    - Line 2-3 (Your Take): Your genuine reaction — a trade-off you see, why it matters (or doesn't), a connection to something you've shipped. Be specific. Be human.
    - Final Line: "Full story:" or "Details:" or "More here:" followed by the source link. Vary this handoff phrasing across the 3 posts.
    - FORMATTING: Double line breaks between thoughts. Maximum 1 emoji. 2-3 hashtags. ZERO markdown.

    FINAL OUTPUT FORMAT:
    Return a valid JSON array of objects. Each object MUST have:
    - "post": The full text of the LinkedIn post.
    - "score": An integer from 1 to 10 predicting the virality and engagement potential.
    - "reasoning": A 1-sentence explanation of why this post is engaging.
    Return ONLY the raw JSON array.

    {articles_context}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,
            top_p=0.95,
            response_mime_type="application/json"
        )
    )
    
    import json
    try:
        drafts = json.loads(response.text.strip())
        drafts.sort(key=lambda x: x.get("score", 0), reverse=True)
    except Exception as e:
        print(f"Error parsing JSON from Gemini: {e}")
        drafts = []
        
    return drafts

def generate_single_draft(articles: list, instruction: str, exclude_drafts: list = None) -> str:
    """Generate a single replacement draft, different from the excluded ones."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set.")
        
    client = genai.Client(api_key=api_key)
    
    articles_context = "Recent News Articles:\n\n"
    for idx, article in enumerate(articles[:30]):
        articles_context += f"{idx+1}. {article['title']}\n"
        articles_context += f"Source: {article['source']}\n"
        articles_context += f"Summary: {article['summary'][:300]}...\n"
        articles_context += f"Link: {article['link']}\n\n"
    
    exclude_context = ""
    if exclude_drafts:
        exclude_context = "\n\nDRAFTS ALREADY GENERATED (write something COMPLETELY different from these — different topic, different angle, different structure):\n"
        for i, d in enumerate(exclude_drafts, 1):
            exclude_context += f"\n--- Existing Draft {i} ---\n{d[:300]}\n"
    
    system_persona = """You are a real person — a senior engineer with 10+ years shipping production systems. \
You write like you talk: direct, a little dry, occasionally funny. You never sound like an AI or a LinkedIn influencer."""

    prompt = f"""
    {system_persona}

    {instruction}
    {exclude_context}

    Write exactly ONE LinkedIn post about a story from the articles below that is NOT covered in the existing drafts.

    VOICE RULES: No filler phrases like "I think", "Here's the thing", "Let that sink in". Write like texting a smart friend. Be specific with technical details.

    STRUCTURE: 3-4 lines max. Hook sentence, your genuine take (1-2 sentences), then "Full story:" or "Details:" with the link. 2-3 hashtags at the bottom.

    FORMATTING: Double line breaks between thoughts. No markdown. Max 1 emoji. Plain text only.

    Output ONLY the post text, nothing else.

    {articles_context}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=1.0,
            top_p=0.95,
        )
    )
    
    return response.text.strip()

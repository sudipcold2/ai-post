import os
import requests
import base64
import urllib.parse
from google import genai
import hashlib

def generate_image_for_post(draft_text: str, group_name: str) -> str:
    """
    Extracts core visual subject from draft using Gemini, then
    generates an image via Pollinations AI based on the specific topic.
    Returns base64 encoded jpeg string.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    visual_subject = group_name
    
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "You are an expert digital artist. Read the following text. "
                    "Write a 1-sentence highly descriptive visual prompt for a striking, conceptual 3D scene representing its core message. "
                    "Focus on physical objects, lighting, and actions. Do NOT mention text, letters, or the word 'image'. "
                    "Example output: 'A glowing robotic hand carefully holding a translucent, futuristic microchip illuminated by blue lasers.'",
                    draft_text
                ]
            )
            if response.text and response.text.strip():
                visual_subject = response.text.strip()
        except Exception as e:
            print("Failed to extract context with Gemini, falling back to group name:", e)
            
    prompt = f"{visual_subject}. Photorealistic, highly detailed, dramatic 3D render, " \
             f"cinematic lighting, rich colors, intricate details, macro photography style, 8k resolution. " \
             f"Premium tech magazine cover art. Absolutely NO text, letters, or watermarks."
    
    # Use deterministic seed based on draft text so same draft yields same image
    seed = int(hashlib.md5(draft_text.encode('utf-8')).hexdigest()[:8], 16)
    
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true&seed={seed}"
    
    response = requests.get(url)
    
    if response.status_code == 200 and response.content:
        return base64.b64encode(response.content).decode('utf-8')
    else:
        raise Exception(f"Pollinations AI failed to generate image. Status Code: {response.status_code}")

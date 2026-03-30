import os
import requests
from dotenv import load_dotenv

load_dotenv()

def post_to_linkedin(content: str) -> bool:
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    urn = os.getenv("LINKEDIN_URN")
    
    if not access_token or not urn:
        raise ValueError("LINKEDIN_ACCESS_TOKEN or LINKEDIN_URN is missing. Please configure your .env file.")
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    
    payload = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
        
    url = "https://api.linkedin.com/v2/ugcPosts"
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        print("Successfully posted to LinkedIn!")
        return True
    else:
        print(f"Failed to post to LinkedIn. Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

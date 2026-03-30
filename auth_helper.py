import os
import urllib.parse
import requests
from dotenv import set_key, load_dotenv

load_dotenv()

# The redirect URI must exactly match the one in your LinkedIn Developer App Auth settings!
REDIRECT_URI = "http://localhost:8000/callback" 
ENV_FILE = ".env"

if not os.path.exists(ENV_FILE):
    # Create an empty .env if it doesn't exist
    open(ENV_FILE, 'a').close()

def main():
    print("--- LinkedIn OAuth 2.0 Helper ---")
    client_id = input("Enter your LinkedIn Client ID (or press Enter to use env): ").strip()
    if not client_id:
        client_id = os.getenv("LINKEDIN_CLIENT_ID")
    
    client_secret = input("Enter your LinkedIn Client Secret (or press Enter to use env): ").strip()
    if not client_secret:
        client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        
    if not client_id or not client_secret:
        print("Error: Client ID and Secret are required.")
        return

    # Step 1: Get Authorization Code
    auth_url = "https://www.linkedin.com/oauth/v2/authorization"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "state": "random_string_123",
        "scope": "w_member_social openid profile email"
    }
    
    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    
    print("\n1. Please make sure that 'http://localhost:8000/callback' is added to your OAuth 2.0 Redirect URLs in the LinkedIn Developer Portal (Auth tab).")
    print("\n2. Click the following URL to authorize the app:")
    print(f"\n{url}\n")
    
    redirect_response = input("3. After authorizing, you will be redirected to a localhost URL. Paste that full URL here:\n> ").strip()
    
    try:
        parsed_url = urllib.parse.urlparse(redirect_response)
        code = urllib.parse.parse_qs(parsed_url.query)['code'][0]
    except Exception as e:
        print("Failed to parse the redirect URL. Make sure you copied the exact URL you were redirected to.")
        return
        
    # Step 2: Get Access Token
    print("\nExchanging code for Access Token...")
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(token_url, data=token_data, headers=headers)
    
    if token_response.status_code != 200:
        print("Error getting access token:", token_response.text)
        return
        
    access_token = token_response.json().get("access_token")
    print("Successfully retrieved Access Token!")
    
    # Step 3: Get User URN
    print("Fetching your LinkedIn URN...")
    userinfo_url = "https://api.linkedin.com/v2/userinfo"
    userinfo_headers = {
        "Authorization": f"Bearer {access_token}"
    }
    userinfo_response = requests.get(userinfo_url, headers=userinfo_headers)
    
    if userinfo_response.status_code != 200:
        print("Error getting user info:", userinfo_response.text)
        urn = "urn:li:person:YOUR_ID_HERE"
    else:
        sub = userinfo_response.json().get("sub")
        urn = f"urn:li:person:{sub}"
        print(f"Successfully retrieved URN: {urn}")
        
    # Step 4: Save to .env
    set_key(ENV_FILE, "LINKEDIN_ACCESS_TOKEN", access_token)
    set_key(ENV_FILE, "LINKEDIN_URN", urn)
    set_key(ENV_FILE, "LINKEDIN_CLIENT_ID", client_id)
    set_key(ENV_FILE, "LINKEDIN_CLIENT_SECRET", client_secret)
    
    print("\nAll done! Your credentials have been saved to .env")

if __name__ == "__main__":
    main()

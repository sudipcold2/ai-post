import os
import json
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_db():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client, Client
            # Force HTTP/1.1 to avoid StreamReset/h2 issues on Render/Supabase
            http_client = httpx.Client(http2=False)
            return create_client(SUPABASE_URL, SUPABASE_KEY, options={"http_client": http_client})
        except Exception as e:
            print(f"Warning: Failed to init Supabase client: {e}")
            return None
    return None

def fetch_config():
    # Attempt with retries for production resilience
    max_retries = 3
    for attempt in range(max_retries):
        db = get_db()
        if db:
            try:
                res = db.table("app_config").select("*").eq("id", "main").execute()
                if res.data:
                    return res.data[0]["config_data"]
                
                # If DB is empty, bootstrap with local config.json if it exists
                if os.path.exists("config.json"):
                    with open("config.json", "r") as f:
                        config = json.load(f)
                    try:
                        db.table("app_config").insert({"id": "main", "config_data": config}).execute()
                    except Exception as e:
                        print(f"Warning: Failed to bootstrap config to Supabase: {e}")
                    return config
                break # Exit loop if successful but empty
            except Exception as e:
                print(f"Attempt {attempt + 1} - Error fetching config from Supabase: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1 * (attempt + 1)) # Simple backoff
                else:
                    print("Max retries reached for Supabase config fetch.")
        else:
            break
            
    # Fallback entirely to local
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {}

def save_config(config_dict):
    db = get_db()
    if db:
        try:
            db.table("app_config").upsert({"id": "main", "config_data": config_dict}).execute()
        except Exception as e:
            print(f"Error saving config to Supabase: {e}")
    else:
        with open("config.json", "w") as f:
            json.dump(config_dict, f, indent=2)

def fetch_history():
    db = get_db()
    if db:
        try:
            res = db.table("post_history").select("*").order("timestamp", desc=True).execute()
            history_list = []
            for row in res.data:
                history_list.append({
                    "timestamp": row["timestamp"],
                    "group": row.get("group_key", ""),
                    "group_name": row.get("group_name", ""),
                    "content": row.get("content", "")
                })
            return history_list
        except Exception as e:
            print(f"Error fetching history from Supabase: {e}")

    # Fallback to local
    if os.path.exists("history.json"):
        with open("history.json", "r") as f:
            try:
                return json.load(f)
            except:
                pass
    return []

def save_history(entry: dict):
    db = get_db()
    if db:
        try:
            db.table("post_history").insert({
                "timestamp": entry["timestamp"],
                "group_key": entry.get("group", ""),
                "group_name": entry.get("group_name", ""),
                "content": entry.get("content", "")
            }).execute()
        except Exception as e:
            print(f"Error saving history to Supabase: {e}")
    else:
        history_list = fetch_history()
        history_list.insert(0, entry)
        with open("history.json", "w") as f:
            json.dump(history_list, f, indent=2)

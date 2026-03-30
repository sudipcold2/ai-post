import os
import json
import time
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# The direct connection string for PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    if DATABASE_URL:
        try:
            # We open a new connection for each master operation for maximum reliability
            # in serverless/free-tier environments, then close it.
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            return conn
        except Exception as e:
            print(f"Warning: Failed to connect to PostgreSQL: {e}")
            return None
    return None

def fetch_config():
    conn = get_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT config_data FROM app_config WHERE id = 'main'")
                row = cur.fetchone()
                if row:
                    return row["config_data"]
                
                # Bootstrap if DB is empty but we have a local config
                if os.path.exists("config.json"):
                    with open("config.json", "r") as f:
                        config = json.load(f)
                    cur.execute(
                        "INSERT INTO app_config (id, config_data) VALUES (%s, %s)",
                        ("main", json.dumps(config))
                    )
                    conn.commit()
                    return config
        except Exception as e:
            print(f"Error fetching config via SQL: {e}")
        finally:
            conn.close()
            
    # Fallback to local
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {}

def save_config(config_dict):
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO app_config (id, config_data) VALUES (%s, %s) "
                    "ON CONFLICT (id) DO UPDATE SET config_data = EXCLUDED.config_data",
                    ("main", json.dumps(config_dict))
                )
                conn.commit()
        except Exception as e:
            print(f"Error saving config via SQL: {e}")
        finally:
            conn.close()
    else:
        with open("config.json", "w") as f:
            json.dump(config_dict, f, indent=2)

def fetch_history():
    conn = get_db()
    if conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT timestamp, group_key as group, group_name, content "
                    "FROM post_history ORDER BY timestamp DESC"
                )
                return cur.fetchall()
        except Exception as e:
            print(f"Error fetching history via SQL: {e}")
        finally:
            conn.close()

    # Fallback to local
    if os.path.exists("history.json"):
        with open("history.json", "r") as f:
            try:
                return json.load(f)
            except:
                pass
    return []

def save_history(entry: dict):
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO post_history (timestamp, group_key, group_name, content) "
                    "VALUES (%s, %s, %s, %s)",
                    (
                        entry["timestamp"],
                        entry.get("group", ""),
                        entry.get("group_name", ""),
                        entry.get("content", "")
                    )
                )
                conn.commit()
        except Exception as e:
            print(f"Error saving history via SQL: {e}")
        finally:
            conn.close()
    else:
        history_list = fetch_history()
        history_list.insert(0, entry)
        with open("history.json", "w") as f:
            json.dump(history_list, f, indent=2)

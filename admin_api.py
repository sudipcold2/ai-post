import os
import secrets
import json
import datetime
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from db import fetch_config, save_config, fetch_history, save_history, fetch_stats

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("admin_ui", exist_ok=True)
app.mount("/static", StaticFiles(directory="admin_ui"), name="static")

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    expected_username = os.getenv("ADMIN_USERNAME", "admin")
    expected_password = os.getenv("ADMIN_PASSWORD", "password")
    
    correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        expected_username.encode("utf8")
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        expected_password.encode("utf8")
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/", response_class=HTMLResponse)
async def get_index(username: str = Depends(authenticate)):
    with open("admin_ui/index.html", "r") as f:
        return f.read()

@app.get("/api/history")
async def get_history(username: str = Depends(authenticate)):
    return fetch_history()

@app.get("/api/config")
async def get_config(username: str = Depends(authenticate)):
    return fetch_config()

@app.get("/api/groups")
async def get_groups(username: str = Depends(authenticate)):
    config = fetch_config()
    groups = config.get("groups", {})
    return [{"key": k, "name": v.get("name", k), "icon": v.get("icon", "🌐")} for k, v in groups.items()]

@app.post("/api/config")
async def update_config(request: Request, username: str = Depends(authenticate)):
    new_config = await request.json()
    save_config(new_config)
    return {"status": "success"}

@app.get("/api/stats")
async def get_stats(username: str = Depends(authenticate)):
    return fetch_stats()

@app.post("/api/draft")
async def draft_post(request: Request, username: str = Depends(authenticate)):
    try:
        from scraper import scrape_articles_for_active_group
        from generator import generate_linkedin_post

        body = {}
        try:
            body = await request.json()
        except:
            pass
        requested_group = body.get("group") if body else None

        config = fetch_config()

        active_group_key = requested_group or config.get("active_group", "ai")

        # Persist active group so scraper picks it up
        config["active_group"] = active_group_key
        save_config(config)

        group_data = config.get("groups", {}).get(active_group_key, {})
        instruction = group_data.get("instruction", "")
        group_name = group_data.get("name", active_group_key)
        group_icon = group_data.get("icon", "🌐")

        articles = scrape_articles_for_active_group()
        if not articles:
            return {"status": "error", "message": "No articles found for this group."}

        drafts = generate_linkedin_post(articles, instruction)
        return {
            "status": "success",
            "drafts": drafts,
            "articles_count": len(articles),
            "group": active_group_key,
            "group_name": group_name,
            "group_icon": group_icon
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/regenerate-single")
async def regenerate_single(request: Request, username: str = Depends(authenticate)):
    """Regenerate a single draft, excluding the other existing drafts."""
    try:
        from scraper import scrape_articles_for_active_group
        from generator import generate_single_draft

        body = await request.json()
        existing_drafts = body.get("existing_drafts", [])
        group_key = body.get("group", "")

        config = fetch_config()
        group_data = config.get("groups", {}).get(group_key, {})
        instruction = group_data.get("instruction", "")

        articles = scrape_articles_for_active_group()
        if not articles:
            return {"status": "error", "message": "No articles found."}

        new_draft = generate_single_draft(articles, instruction, exclude_drafts=existing_drafts)
        return {"status": "success", "draft": new_draft}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-image")
async def generate_image_endpoint(request: Request, username: str = Depends(authenticate)):
    try:
        from image_gen import generate_image_for_post
        data = await request.json()
        draft_text = data.get("draft")
        group_name = data.get("group_name", "Tech News")
        
        b64 = generate_image_for_post(draft_text, group_name)
        return {"status": "success", "image_base64": b64}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/publish")
async def publish_post_endpoint(request: Request, username: str = Depends(authenticate)):
    try:
        data = await request.json()
        content = data.get("content")
        group = data.get("group", "")
        group_name = data.get("group_name", group)
        image_base64 = data.get("image_base64")

        from linkedin_poster import post_to_linkedin
        success = post_to_linkedin(content, image_base64=image_base64)

        if success:
            save_history({
                "timestamp": datetime.datetime.now().isoformat(),
                "group": group,
                "group_name": group_name,
                "content": content
            })
            return {"status": "success"}
        else:
            return {"status": "error", "message": "Failed to post to LinkedIn."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)

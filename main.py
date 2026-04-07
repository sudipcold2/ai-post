import time
import schedule
import datetime
from scraper import scrape_articles_for_active_group
from generator import generate_linkedin_post
from linkedin_poster import post_to_linkedin
from db import fetch_config, save_history

def job():
    print("Starting scheduled LinkedIn Poster job...")
    
    try:
        config = fetch_config()
        
        active_group_key = config.get("active_group", "ai")
        group_data = config.get("groups", {}).get(active_group_key, {})
        instruction = group_data.get("instruction", "Write an engaging LinkedIn post.")
        group_name = group_data.get("name", active_group_key)
        
        print(f"Scraping articles for group: {active_group_key} ({group_name})...")
        articles = scrape_articles_for_active_group()
        
        if not articles:
            print("No articles found to post today. Skipping.")
            return
            
        print(f"Found {len(articles)} articles. Generating post...")
        drafts = generate_linkedin_post(articles, instruction)
        if isinstance(drafts, list) and len(drafts) > 0:
            post_content = drafts[0].get("post", "") if isinstance(drafts[0], dict) else drafts[0]
        else:
            post_content = str(drafts)
        
        print("\n--- Generated Post Preview ---")
        print(post_content)
        print("------------------------------\n")
        
        print("Posting to LinkedIn...")
        success = post_to_linkedin(post_content)
        
        if success:
            print("Job completed successfully!")
            save_history({
                "timestamp": datetime.datetime.now().isoformat(),
                "group": active_group_key,
                "group_name": group_name,
                "content": post_content
            })
            
    except Exception as e:
        print(f"An error occurred during the job: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running in test mode (immediate execution)...")
        job()
    else:
        run_time = "09:00"
        schedule.every().day.at(run_time).do(job)
        
        print(f"Scheduler started. Job will run daily at {run_time}.")
        print("Use 'python main.py --test' to run immediately without scheduling.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

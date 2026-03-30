import time
import schedule
import json
import os
import datetime
from scraper import scrape_articles_for_active_topic
from generator import generate_linkedin_post
from linkedin_poster import post_to_linkedin

def job():
    print("Starting scheduled LinkedIn Poster job...")
    
    try:
        # Read config
        with open("config.json", "r") as f:
            config = json.load(f)
        
        active_topic_key = config.get("active_topic", "ai")
        instruction = config.get("topics", {}).get(active_topic_key, {}).get("instruction", "Write an engaging LinkedIn post.")
        
        print(f"Scraping articles for topic: {active_topic_key}...")
        articles = scrape_articles_for_active_topic()
        
        if not articles:
            print("No articles found to post today. Skipping.")
            return
            
        print(f"Found {len(articles)} articles. Generating post...")
        drafts = generate_linkedin_post(articles, instruction)
        post_content = drafts[0] if isinstance(drafts, list) and len(drafts) > 0 else str(drafts)
        
        print("\n--- Generated Post Preview ---")
        print(post_content)
        print("------------------------------\n")
        
        print("Posting to LinkedIn...")
        success = post_to_linkedin(post_content)
        
        if success:
            print("Job completed successfully!")
            
            # Log to history.json
            history_file = "history.json"
            history_data = []
            if os.path.exists(history_file):
                with open(history_file, "r") as hf:
                    try:
                        history_data = json.load(hf)
                    except:
                        history_data = []
            
            history_data.insert(0, {
                "timestamp": datetime.datetime.now().isoformat(),
                "topic": active_topic_key,
                "content": post_content
            })
            
            with open(history_file, "w") as hf:
                json.dump(history_data, hf, indent=2)
            
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

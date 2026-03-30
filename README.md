# 🤖 AI Poster: Autonomous News Engine & LinkedIn Poster

An autonomous AI-powered news engine that aggregates high-signal technical updates from global AI labs, generates engagement-optimized LinkedIn post variations, and provides a modern glassmorphism dashboard for one-click publishing.

![Admin Dashboard](https://raw.githubusercontent.com/sudipcold2/ai-post/main/admin_ui/screenshot_placeholder.png) *(Modern, Mobile-Friendly Admin UI)*

## ✨ Features

- **Autonomous Scraping**: Aggregates news from top-tier research blogs (OpenAI, Anthropic, DeepMind, Meta AI) and engineering communities (Hacker News, Lobsters).
- **AI-Powered Ranking**: Uses Gemini 1.5 Pro to rank articles based on backend architectural impact and technical depth (skipping the hype).
- **Smart Variations**: Generates multiple LinkedIn post variations tailored for different engineering audiences.
- **Modern Admin Dashboard**: A premium, "glassmorphism" web UI for reviewing drafts, editing content, and viewing post history.
- **Fully Responsive**: Optimized for both high-end desktop displays and mobile-on-the-go management.
- **Enterprise Ready**: Integrated with Supabase for cloud-hosted history and configuration, but falls back to local JSON for zero-cost development.

## 🚀 Tech Stack

- **Backend**: FastAPI (Python)
- **AI**: Google Gemini Pro (via Generative AI SDK)
- **Database**: Supabase (PostgreSQL) / Local JSON fallback
- **Frontend**: Vanilla Javascript & Modern CSS (Glassmorphism design system)
- **Deployment**: Configured for Render and Supabase

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- Python 3.11+
- [Gemini API Key](https://aistudio.google.com/app/apikey)
- [LinkedIn Developer App](https://developer.linkedin.com/oss-applications) (for `w_member_social` permissions)
- [Supabase Project](https://supabase.com/) (Optional: for cloud persistence)

### 2. Clone and Install
```bash
git clone git@github.com:sudipcold2/ai-post.git
cd ai-post

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Copy the example environment file and fill in your credentials:
```bash
cp .env.example .env
```

### 4. LinkedIn Authentication
Run the helper script to obtain your LinkedIn access token and URN:
```bash
python auth_helper.py
```
Follow the interactive prompts to authorize your app and save the credentials to `.env`.

---

## 🖥️ Usage

### Running Locally
Start the admin dashboard:
```bash
python admin_api.py
```
Access the panel at `http://127.0.0.1:8080`.

### Workflow
1. **Choose Category**: Select from AI, Big Tech, Distributed Systems, etc.
2. **Draft New Options**: Click "Draft" to scrape the latest news and generate AI post variations.
3. **Review & Edit**: Pick your favorite draft, tweak the text in the glass editor.
4. **Publish**: Click "Publish" to send the post directly to your LinkedIn feed.

---

## 📂 Project Structure

```text
├── admin_api.py      # FastAPI backend for the dashboard
├── admin_ui/         # Static frontend assets (HTML, CSS, JS)
├── generator.py      # AI core for processing news and generating drafts
├── scraper.py        # RSS and web scraping engine
├── linkedin_poster.py # LinkedIn API integration
├── auth_helper.py    # OAuth 2.0 helper for LinkedIn
├── db.py             # Dual-mode (Supabase/JSON) data layer
└── render.yaml       # Render.com blueprint config
```

---

## 📜 License
This project is licensed under the MIT License.

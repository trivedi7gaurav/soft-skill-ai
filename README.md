# Soft Skills AI — Hosted Web App

A mobile-friendly, hosted version of the Soft Skills AI coach. Free to run,
accessible from your phone, laptop, or any device with a browser once deployed.

## What changed from the CLI version

- **LLM backend:** Groq's free API (fast, no cost, no self-hosting) instead of local Ollama
- **Database:** Supabase's free Postgres (persists forever, works across all your devices)
- **Frontend:** a mobile-friendly chat page, served by the same app — one URL, works everywhere
- **Memory:** two upgrades —
  1. Your past conversations load automatically when you log in with the same name
  2. A running "profile summary" is built from everything you've told any agent,
     and every agent sees it — so telling Interview about your job also helps
     Coach give better advice

## Step-by-step deployment (about 15 minutes, no card required)

### 1. Get a free Groq API key
1. Go to **https://console.groq.com/keys**
2. Sign up (free, no credit card)
3. Click "Create API Key", copy it somewhere safe — you'll paste it in step 3

### 2. Create a free Supabase database
1. Go to **https://supabase.com** and sign up (free, no credit card)
2. Click "New Project", give it any name, set a database password (write it down)
3. Once it's created, go to **Project Settings → Database → Connection string → URI**
4. Copy that connection string — you'll paste it in step 3
   (it looks like `postgresql://postgres:[password]@...supabase.co:5432/postgres`)

### 3. Deploy to Render (free, always-on URL)
1. Go to **https://render.com** and sign up (free, no credit card)
2. Push this project folder to a GitHub repo (or use Render's "Deploy from a
   public Git repo" option if you'd rather not set up Git — ask me and I can
   walk you through either path)
3. In Render, click **New → Web Service**, connect your repo
4. Render will detect `render.yaml` automatically. If it asks, set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment**, add two variables:
   - `GROQ_API_KEY` → paste your key from step 1
   - `DATABASE_URL` → paste your connection string from step 2
6. Click **Deploy**. After a minute or two, Render gives you a live URL like
   `https://soft-skills-ai.onrender.com`

### 4. Use it
Open that URL on your phone, laptop, tablet — anywhere. Bookmark it or add it
to your home screen for quick access. Log in with the same name each time to
keep your history and progress.

## Notes on the free tier

- Render's free web service "sleeps" after 15 minutes of no traffic, and takes
  20-30 seconds to wake up on the next visit. That's normal — just a one-time
  wait, not a bug.
- Groq's free tier has generous but real rate limits. If you hit them, you'll
  see an error asking you to wait a bit before trying again.
- Supabase's free tier persists your data indefinitely as long as the project
  stays active (it can pause after ~1 week of total inactivity, but reactivates
  automatically the next time you use it — no data lost).

## Local testing before deploying (optional)

If you want to test on your own machine first:

```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here
export DATABASE_URL=your_supabase_connection_string_here
uvicorn main:app --reload
```

Then open **http://localhost:8000** in your browser.

## Architecture

```
main.py              FastAPI app: API routes + serves the frontend
config.py             Reads GROQ_API_KEY / DATABASE_URL from environment
llm_client.py          Groq API client (chat + structured JSON calls)
database.py            Postgres persistence: users, messages, assessments, plans
memory.py              Cross-agent long-term profile summary
agents/
  base_agent.py         Shared logic: cross-agent history + profile injection
  coach_agent.py         Communication/leadership/EQ coaching
  interview_agent.py     Mock interviews with structured feedback
  assessment_agent.py    Scores 6 soft skills from conversation history
  learning_plan_agent.py Generates a personalized plan from scores
  router.py              Intent classifier (used by the frontend's "auto" mode)
static/
  index.html            Mobile-friendly single-page chat UI
render.yaml            Render deployment config
```

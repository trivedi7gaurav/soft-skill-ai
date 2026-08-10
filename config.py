"""
Configuration for the hosted Soft Skills AI web app.

All secrets come from environment variables (set them in Render's dashboard,
never commit them to code):
  GROQ_API_KEY   - free API key from https://console.groq.com/keys
  DATABASE_URL   - Postgres connection string from https://supabase.com
                   (Project Settings -> Database -> Connection string -> URI)
"""

import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

DATABASE_URL = os.environ.get("DATABASE_URL", "")

DEFAULT_TEMPERATURE = 0.7
REQUEST_TIMEOUT_SECONDS = 60

"""
Soft Skills AI - hosted web app.

Serves a JSON API plus a single-page mobile-friendly frontend
(static/index.html) that talks to it.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import database
from agents.coach_agent import CoachAgent
from agents.interview_agent import InterviewAgent
from agents.assessment_agent import AssessmentAgent
from agents import router as intent_router
from agents import learning_plan_agent
import llm_client

app = FastAPI(title="Soft Skills AI")

AGENT_CLASSES = {
    "coach": CoachAgent,
    "interview": InterviewAgent,
    "assessment": AssessmentAgent,
}


@app.on_event("startup")
def on_startup():
    database.init_db()


# ---------- Request/response models ----------

class LoginRequest(BaseModel):
    name: str
    domain: str = "general"


class ChatRequest(BaseModel):
    user_id: int
    agent: str  # "coach" | "interview" | "assessment" | "auto"
    message: str


class ScoreRequest(BaseModel):
    user_id: int


class PlanRequest(BaseModel):
    user_id: int


# ---------- API routes ----------

@app.post("/api/login")
def login(req: LoginRequest):
    name = req.name.strip()
    if not name:
        raise HTTPException(400, "Name is required")

    user_id, profile_summary = database.get_or_create_user(name, req.domain)

    history = database.get_recent_messages(user_id, limit=30, agent=None)
    assessments = database.get_latest_assessments(user_id)
    plan, plan_created_at = database.get_latest_learning_plan(user_id)

    return {
        "user_id": user_id,
        "profile_summary": profile_summary,
        "history": [dict(h) for h in history],
        "assessments": [dict(a) for a in assessments],
        "learning_plan": plan,
        "learning_plan_created_at": plan_created_at,
    }


@app.post("/api/chat")
def chat(req: ChatRequest):
    agent_key = req.agent
    if agent_key == "auto":
        agent_key = intent_router.route(req.message)

    agent_cls = AGENT_CLASSES.get(agent_key)
    if not agent_cls:
        raise HTTPException(400, f"Unknown agent '{req.agent}'")

    agent = agent_cls(req.user_id)
    try:
        reply = agent.say(req.message)
    except llm_client.LLMError as e:
        raise HTTPException(502, str(e))

    return {"agent": agent_key, "reply": reply}


@app.post("/api/assessment/score")
def score(req: ScoreRequest):
    agent = AssessmentAgent(req.user_id)
    try:
        scores, notes = agent.run_scoring()
    except llm_client.LLMError as e:
        raise HTTPException(502, str(e))
    return {"scores": scores, "notes": notes}


@app.post("/api/learning-plan")
def learning_plan(req: PlanRequest):
    try:
        plan = learning_plan_agent.generate_plan(req.user_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except llm_client.LLMError as e:
        raise HTTPException(502, str(e))
    return {"plan": plan}


@app.get("/api/history/{user_id}")
def history(user_id: int, agent: str = None):
    rows = database.get_recent_messages(user_id, limit=50, agent=agent)
    return {"history": [dict(r) for r in rows]}


# ---------- Frontend ----------

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")

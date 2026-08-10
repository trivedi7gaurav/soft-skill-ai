"""
Postgres persistence layer (hosted on Supabase's free tier).
Same shape as the original SQLite version, plus a `profile_summary` column
on users for long-term cross-agent memory.
"""

import json
from datetime import datetime, timezone
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

import config


def _now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_conn():
    conn = psycopg2.connect(config.DATABASE_URL)
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                domain TEXT DEFAULT 'general',
                profile_summary TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                agent TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS assessments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                skill TEXT NOT NULL,
                score INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS learning_plans (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                plan_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def get_or_create_user(name: str, domain: str = "general"):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, profile_summary FROM users WHERE name = %s", (name,))
        row = cur.fetchone()
        if row:
            return row["id"], row["profile_summary"] or ""
        cur.execute(
            "INSERT INTO users (name, domain, profile_summary, created_at) "
            "VALUES (%s, %s, '', %s) RETURNING id",
            (name, domain, _now()),
        )
        new_id = cur.fetchone()["id"]
        return new_id, ""


def get_profile_summary(user_id: int) -> str:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT profile_summary FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] else ""


def update_profile_summary(user_id: int, summary: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET profile_summary = %s WHERE id = %s", (summary, user_id)
        )


def save_message(user_id: int, agent: str, role: str, content: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (user_id, agent, role, content, created_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, agent, role, content, _now()),
        )


def get_recent_messages(user_id: int, limit: int = 12, agent: str = None):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if agent:
            cur.execute(
                "SELECT agent, role, content, created_at FROM messages "
                "WHERE user_id = %s AND agent = %s ORDER BY id DESC LIMIT %s",
                (user_id, agent, limit),
            )
        else:
            cur.execute(
                "SELECT agent, role, content, created_at FROM messages "
                "WHERE user_id = %s ORDER BY id DESC LIMIT %s",
                (user_id, limit),
            )
        rows = cur.fetchall()
    return list(reversed(rows))


def save_assessment(user_id: int, skill: str, score: int, notes: str = ""):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO assessments (user_id, skill, score, notes, created_at) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, skill, score, notes, _now()),
        )


def get_latest_assessments(user_id: int):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT skill, score, notes, created_at
            FROM assessments a
            WHERE user_id = %s AND created_at = (
                SELECT MAX(created_at) FROM assessments b
                WHERE b.user_id = a.user_id AND b.skill = a.skill
            )
            """,
            (user_id,),
        )
        return cur.fetchall()


def save_learning_plan(user_id: int, plan: dict):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO learning_plans (user_id, plan_json, created_at) "
            "VALUES (%s, %s, %s)",
            (user_id, json.dumps(plan), _now()),
        )


def get_latest_learning_plan(user_id: int):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT plan_json, created_at FROM learning_plans "
            "WHERE user_id = %s ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
    if row:
        return json.loads(row["plan_json"]), row["created_at"]
    return None, None

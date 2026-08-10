import database
import llm_client
from agents.base_agent import BaseAgent

SKILLS = [
    "communication",
    "leadership",
    "empathy",
    "problem_solving",
    "presentation",
    "interview_readiness",
]

_SCORING_SYSTEM_PROMPT = (
    "You are a soft-skills assessor. Based on the conversation transcript provided, "
    "score the person on each of these skills from 1 (needs significant development) "
    "to 10 (excellent), using only evidence actually present in the transcript. "
    "If there isn't enough evidence for a skill, give your best conservative estimate "
    "(default 5) and say so in the notes.\n\n"
    f"Skills to score: {', '.join(SKILLS)}.\n\n"
    'Return JSON exactly in this shape:\n'
    '{"scores": {"communication": 7, "leadership": 5, "empathy": 6, '
    '"problem_solving": 6, "presentation": 5, "interview_readiness": 5}, '
    '"notes": {"communication": "short reason", ...}}'
)


class AssessmentAgent(BaseAgent):
    name = "assessment"
    system_prompt = (
        "You are 'Assessment', a friendly evaluator. Ask the user 3-4 short questions "
        "about a recent work/school situation involving communication, teamwork, or "
        "problem-solving so you have enough material to score their soft skills. "
        "Ask one question at a time. Keep it light and conversational."
    )

    def run_scoring(self):
        rows = database.get_recent_messages(self.user_id, limit=40, agent=None)
        transcript = "\n".join(f"{r['role']} ({r['agent']}): {r['content']}" for r in rows)

        if not transcript.strip():
            transcript = "(No conversation yet.)"

        result = llm_client.chat_json(
            _SCORING_SYSTEM_PROMPT,
            [{"role": "user", "content": f"Transcript:\n{transcript}"}],
        )

        scores = result.get("scores", {})
        notes = result.get("notes", {})

        for skill, score in scores.items():
            try:
                score_int = int(score)
            except (TypeError, ValueError):
                continue
            database.save_assessment(self.user_id, skill, score_int, notes.get(skill, ""))

        return scores, notes

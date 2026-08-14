import database
import llm_client

_PLAN_SYSTEM_PROMPT = (
    "You are a personalized learning-plan generator for a soft-skills coaching platform. "
    "Given a user's latest skill scores (1-10), produce a focused 2-week improvement plan.\n\n"
    "Return JSON exactly in this shape:\n"
    "{\n"
    '  "focus_skills": ["skill1", "skill2"],\n'
    '  "summary": "1-2 sentence overview",\n'
    '  "days": [\n'
    '    {"day": 1, "focus": "skill", "activity": "specific exercise", "goal": "what success looks like"},\n'
    "    ... (aim for 5-8 concrete days, not all 14 need to be listed)\n"
    "  ]\n"
    "}\n"
    "Prioritize the 2-3 lowest-scoring skills. Make activities concrete and doable in "
    "15-30 minutes (e.g. 'Record yourself giving a 2-minute self-introduction and review filler words')."
)


def generate_plan(user_id: int) -> dict:
    assessments = database.get_latest_assessments(user_id)

    if not assessments:
        raise ValueError(
            "No assessment data yet. Run a Skill Assessment first so the plan "
            "can be personalized to real scores."
        )

    scores_summary = "\n".join(f"- {a['skill']}: {a['score']}/10 ({a['notes']})" for a in assessments)

    plan = llm_client.chat_json(
        _PLAN_SYSTEM_PROMPT,
        [{"role": "user", "content": f"Latest scores:\n{scores_summary}"}],
    )

    database.save_learning_plan(user_id, plan)
    return plan

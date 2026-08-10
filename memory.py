"""
Long-term cross-agent memory.

After each user turn, we ask the LLM to fold any new, durable facts about the
user (their role, goals, recurring struggles, preferences) into a short
running profile summary. This summary is then injected into every agent's
system prompt, so the Coach, Interview, and Assessment agents all "know"
things the user only ever told a different agent.

Kept deliberately short (a paragraph, not a transcript) so it stays cheap
to include in every request.
"""

import database
import llm_client

_MEMORY_SYSTEM_PROMPT = (
    "You maintain a short running profile of a user for a soft-skills coaching "
    "app. You will be given the EXISTING profile summary (may be empty) and the "
    "MOST RECENT exchange. Update the summary to include any new durable facts "
    "worth remembering: their role/domain, goals, recurring challenges, "
    "preferences, or notable context. Do NOT include one-off details that don't "
    "matter long-term. Keep the result under 100 words, written as plain "
    "prose (not a list). If nothing new and durable was said, return the "
    "existing summary unchanged.\n\n"
    'Return JSON exactly like: {"summary": "..."}'
)


def update_profile_after_turn(user_id: int, user_text: str, assistant_text: str):
    """
    Best-effort update; failures here should never break the chat flow,
    so callers should wrap this in a try/except.
    """
    existing = database.get_profile_summary(user_id)

    result = llm_client.chat_json(
        _MEMORY_SYSTEM_PROMPT,
        [
            {
                "role": "user",
                "content": (
                    f"EXISTING profile summary:\n{existing or '(empty)'}\n\n"
                    f"MOST RECENT exchange:\nUser: {user_text}\nAssistant: {assistant_text}"
                ),
            }
        ],
        temperature=0.2,
    )

    new_summary = result.get("summary", "").strip()
    if new_summary:
        database.update_profile_summary(user_id, new_summary)
    return new_summary

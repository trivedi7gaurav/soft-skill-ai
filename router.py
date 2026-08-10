import llm_client

_ROUTES = {
    "coach": "General communication, leadership, negotiation, EQ, conflict, career advice",
    "interview": "Practicing for a job interview, mock interview questions",
    "assessment": "Wants to be evaluated / scored / assessed on their soft skills",
}

_ROUTER_SYSTEM_PROMPT = (
    "You are an intent router for a soft-skills coaching app. Given the user's message, "
    "choose exactly one route from this list:\n"
    + "\n".join(f"- {k}: {v}" for k, v in _ROUTES.items())
    + "\n\nReturn JSON exactly like: {\"route\": \"coach\"}"
)


def route(user_text: str) -> str:
    try:
        result = llm_client.chat_json(
            _ROUTER_SYSTEM_PROMPT,
            [{"role": "user", "content": user_text}],
        )
        choice = result.get("route", "coach")
        return choice if choice in _ROUTES else "coach"
    except llm_client.LLMError:
        text = user_text.lower()
        if "interview" in text:
            return "interview"
        if "assess" in text or "score" in text or "evaluate" in text:
            return "assessment"
        return "coach"

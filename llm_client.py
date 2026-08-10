"""
Client for Groq's free-tier LLM API (OpenAI-compatible /chat/completions).
Get a free key at https://console.groq.com/keys - no credit card required.
"""

import json
import requests

import config


class LLMError(RuntimeError):
    pass


def chat(system_prompt: str, messages: list, temperature: float = None) -> str:
    if not config.GROQ_API_KEY:
        raise LLMError(
            "GROQ_API_KEY is not set. Get a free key at "
            "https://console.groq.com/keys and add it as an environment "
            "variable on your hosting platform."
        )

    payload = {
        "model": config.GROQ_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": temperature if temperature is not None else config.DEFAULT_TEMPERATURE,
    }
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            config.GROQ_API_URL,
            json=payload,
            headers=headers,
            timeout=config.REQUEST_TIMEOUT_SECONDS,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise LLMError(f"Groq API error: {resp.text}") from e
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Could not reach Groq API: {e}") from e

    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def chat_json(system_prompt: str, messages: list, temperature: float = 0.2) -> dict:
    strict_system = (
        system_prompt
        + "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown fences, "
        "no commentary, no preamble."
    )
    raw = chat(strict_system, messages, temperature=temperature)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise LLMError(f"Model did not return valid JSON:\n{raw}")

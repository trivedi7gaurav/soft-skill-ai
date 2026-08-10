"""
Base class for all specialized agents. Now memory-aware:
- Loads recent history from ALL agents (not just this one), so switching
  from Coach to Interview doesn't lose context.
- Injects the user's long-term profile_summary into the system prompt.
- Updates that profile summary after every turn (best-effort).
"""

import database
import llm_client
import memory


class BaseAgent:
    name = "base"
    system_prompt = "You are a helpful assistant."

    def __init__(self, user_id: int):
        self.user_id = user_id

    def _history_as_messages(self, limit: int = 16):
        # Cross-agent history: whichever agent responds, it sees the whole
        # recent conversation, not just its own slice.
        rows = database.get_recent_messages(self.user_id, limit=limit, agent=None)
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    def _full_system_prompt(self):
        profile = database.get_profile_summary(self.user_id)
        if profile:
            return (
                f"{self.system_prompt}\n\n"
                f"What you know about this user so far (from earlier sessions "
                f"and other agents in this app): {profile}"
            )
        return self.system_prompt

    def say(self, user_text: str) -> str:
        database.save_message(self.user_id, self.name, "user", user_text)

        history = self._history_as_messages()
        reply = llm_client.chat(self._full_system_prompt(), history)

        database.save_message(self.user_id, self.name, "assistant", reply)

        try:
            memory.update_profile_after_turn(self.user_id, user_text, reply)
        except llm_client.LLMError:
            pass  # memory update is best-effort; never break the chat

        return reply

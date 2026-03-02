import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class Roaster:
    """Generate honest, contextual responses using Claude with full history."""

    @staticmethod
    async def roast_with_context(
        user_message: str,
        user_id: int,
        session: dict,
        shared_memory_context: Optional[str] = None,
        conversation_history: Optional[list] = None,
        input_handler=None,
    ) -> Tuple[str, Optional[str]]:
        """
        Generate an honest response using Claude with full context.

        Args:
            user_message: What the user just said
            user_id: The user's ID
            session: Claude Code session info
            shared_memory_context: Shared memory across chats
            conversation_history: User's past conversations
            input_handler: Handler to call Claude

        Returns:
            Tuple of (response, error)
        """

        if not input_handler:
            logger.error("❌ input_handler is None - Claude CLI not available")
            return "Got it.", None

        if not session:
            logger.error("❌ session is None - Claude Code not running")
            return "Got it.", None

        # Build context from conversation history
        history_context = Roaster._build_history_context(conversation_history)

        # Build the prompt with full context
        prompt = Roaster._build_prompt(
            user_message,
            history_context,
            shared_memory_context,
        )

        logger.info(f"📝 Built prompt ({len(prompt)} chars) for user {user_id}")
        logger.info(f"Sending to Claude from session: {session.get('sessionId')}")

        # Call Claude to generate response
        response, error = input_handler.send_to_claude(prompt, session)

        if error:
            logger.error(f"❌ Claude error: {error}")
            return None, error

        if not response:
            logger.warning(f"❌ Claude returned empty response")
            return None, "No response from Claude"

        logger.info(f"✅ Claude responded ({len(response)} chars): {response[:100]}")

        # Claude returns the direct response (keep it as-is, Claude knows to be brief)
        return response.strip(), None

    @staticmethod
    def _build_history_context(conversation_history: Optional[list]) -> str:
        """Build context from user's conversation history (user messages only, not bot responses)."""
        if not conversation_history or len(conversation_history) == 0:
            return ""

        # Get last 10 user messages for context (not bot responses)
        recent = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history

        history_lines = ["Recent things this user has said:"]
        for conv in recent:
            user_msg = conv.get("user_message", "").strip()
            if user_msg:  # Only include non-empty user messages
                history_lines.append(f"  • {user_msg}")

        return "\n".join(history_lines)

    @staticmethod
    def _build_prompt(
        user_message: str,
        history_context: str,
        shared_memory_context: Optional[str] = None,
    ) -> str:
        """Build the prompt for Claude with all context."""

        prompt_parts = [
            "You are Clodbotty, a helpful bot in friend group chats who finds humor when it naturally emerges.",
            "Your job: Respond honestly. Find genuine humor opportunities, but don't force it.",
            "",
            "PRIORITIES (in order):",
            "1. BE HONEST & HELPFUL - This is your foundation",
            "2. FIND HUMOR NATURALLY - Only if there's a genuine, original joke or observation",
            "3. BE CONTEXTUAL - Reference what they actually said + their past patterns",
            "4. KNOW WHEN TO BE SILENT - If you have nothing funny or useful to add, don't respond",
            "5. KEEP IT SHORT - 1-2 sentences max",
            "",
            "HUMOR GUIDELINES:",
            "- Only be sarcastic or joke when it's TRULY funny, not forced",
            "- Look for original observations based on their patterns",
            "- Self-deprecation works when genuine (acknowledging you're a bot)",
            "- Never respond just to respond - silence is better than filler",
            "",
            "CONTEXT YOU HAVE:",
            "- What they just said (below)",
            "- Their recent messages (what they've been talking about)",
            "- Shared memory (patterns across all chats, running jokes)",
            "",
            "ANDREW'S KNOWN PATTERNS (reference if genuinely relevant):",
            "- OneDrive storage issues on Windows",
            "- Subprocess/event loop problems on Windows",
            "- Tests code once, confident it works, breaks elsewhere",
            "- Builds experimental bots (I'm one of them!)",
            "",
        ]

        if history_context:
            prompt_parts.append("RECENT CONVERSATIONS WITH THIS USER:")
            prompt_parts.append(history_context)
            prompt_parts.append("")

        if shared_memory_context:
            prompt_parts.append("RUNNING JOKES & PATTERNS (from all chats):")
            prompt_parts.append(shared_memory_context)
            prompt_parts.append("")

        prompt_parts.append("=" * 50)
        prompt_parts.append("")
        prompt_parts.append(f"WHAT THEY JUST SAID: {user_message}")
        prompt_parts.append("")
        prompt_parts.append("RESPOND HONESTLY. IF THERE'S A GENUINE JOKE/OBSERVATION, INCLUDE IT (1-2 SENTENCES MAX).")

        return "\n".join(prompt_parts)

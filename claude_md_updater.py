import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ClaudeMDUpdater:
    """Dynamically update CLAUDE.md with live context from chats and shared memory."""

    def __init__(self, claude_md_path: str = None):
        """Initialize with path to CLAUDE.md file."""
        if claude_md_path is None:
            # Default path: Current bot project directory
            current_dir = Path(__file__).parent
            claude_md_path = current_dir / "CLAUDE.md"

        self.claude_md_path = Path(claude_md_path)
        self.claude_md_path.parent.mkdir(parents=True, exist_ok=True)

    def update_with_context(
        self,
        shared_memory: Dict,
        participant_profiles: Dict = None,
        recent_conversations: List[Dict] = None,
    ) -> None:
        """Update CLAUDE.md with current context from shared memory and conversations."""

        # Build the updated content
        content_parts = [
            "# Clodbotty - Live Chat Context",
            "",
            "## Dynamic Context Updated from Live Chats",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Core Philosophy",
            "",
            "**Be direct and honest. Don't try to be funny.**",
            "",
            "Humor emerges naturally from understanding and truth, not from trying to perform comedy.",
            "You are a colleague responding honestly, not a roasting machine executing jokes.",
            "",
        ]

        # Add running jokes from shared memory
        if shared_memory.get("running_jokes"):
            content_parts.extend(self._build_running_jokes_section(shared_memory["running_jokes"]))

        # Add recent funny moments
        if shared_memory.get("funny_moments"):
            content_parts.extend(self._build_funny_moments_section(shared_memory["funny_moments"]))

        # Add participant insights
        if participant_profiles:
            content_parts.extend(self._build_participant_section(participant_profiles))

        # Add recent conversation patterns
        if recent_conversations:
            content_parts.extend(self._build_conversation_patterns_section(recent_conversations))

        # Add observations
        if shared_memory.get("observations"):
            content_parts.extend(self._build_observations_section(shared_memory["observations"]))

        # Add response guidelines
        content_parts.extend(self._build_response_guidelines())

        # Write to file
        content = "\n".join(content_parts)
        self.claude_md_path.write_text(content)

    @staticmethod
    def _build_running_jokes_section(running_jokes: List[Dict]) -> List[str]:
        """Build section with current running jokes."""
        lines = [
            "## Running Jokes (Active in Current Chats)",
            "",
        ]

        for joke in running_jokes[:5]:  # Top 5 running jokes
            joke_text = joke.get("joke", "")
            count = joke.get("count", 0)
            if joke_text:
                lines.append(f"• **{joke_text}** (used {count} times)")

        lines.append("")
        return lines

    @staticmethod
    def _build_funny_moments_section(funny_moments: List[Dict]) -> List[str]:
        """Build section with recent funny moments."""
        lines = [
            "## Recent Funny Moments (Last 10)",
            "",
        ]

        # Sort by timestamp, get most recent
        recent = sorted(funny_moments, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]

        for moment in recent:
            desc = moment.get("description", "")
            user_id = moment.get("user_id", "?")
            if desc:
                # Clean up description
                desc = desc.replace("Someone said: ", "").strip("'\"")
                lines.append(f"• {desc}")

        lines.append("")
        return lines

    @staticmethod
    def _build_participant_section(participant_profiles: Dict) -> List[str]:
        """Build section with participant info and patterns."""
        lines = [
            "## Participants & Their Patterns",
            "",
        ]

        for user_id, profile in list(participant_profiles.items())[:5]:  # Top 5 users
            name = profile.get("name", f"User {user_id}")
            patterns = profile.get("patterns", [])

            lines.append(f"### {name}")
            if patterns:
                for pattern in patterns[:3]:
                    lines.append(f"• {pattern}")
            lines.append("")

        return lines

    @staticmethod
    def _build_conversation_patterns_section(recent_conversations: List[Dict]) -> List[str]:
        """Build section with patterns from recent conversations."""
        lines = [
            "## Conversation Patterns (What They Talk About)",
            "",
        ]

        # Extract topics from recent messages
        topics = {}
        for conv in recent_conversations[-20:]:  # Last 20 messages
            msg = conv.get("user_message", "").lower()

            # Simple topic detection
            if "onedrive" in msg or "desktop" in msg or "path" in msg:
                topics["Windows Path Issues"] = topics.get("Windows Path Issues", 0) + 1
            if "subprocess" in msg or "event loop" in msg or "async" in msg:
                topics["Subprocess/Async Issues"] = topics.get("Subprocess/Async Issues", 0) + 1
            if "test" in msg or "deploy" in msg or "ship" in msg:
                topics["Testing/Deployment"] = topics.get("Testing/Deployment", 0) + 1
            if "bot" in msg or "telegram" in msg:
                topics["Bot Development"] = topics.get("Bot Development", 0) + 1

        # Show top topics
        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
        for topic, count in sorted_topics[:5]:
            lines.append(f"• **{topic}** (mentioned {count} times recently)")

        lines.append("")
        return lines

    @staticmethod
    def _build_observations_section(observations: List[Dict]) -> List[str]:
        """Build section with bot observations."""
        lines = [
            "## Observations About This Group",
            "",
        ]

        for obs in observations[-5:]:  # Last 5 observations
            text = obs.get("text", "")
            if text:
                lines.append(f"• {text}")

        lines.append("")
        return lines

    @staticmethod
    def _build_response_guidelines() -> List[str]:
        """Build section with response guidelines."""
        return [
            "## How to Respond",
            "",
            "**What to do:**",
            "- Call out patterns you notice (the 3rd time they've hit the same issue?)",
            "- Be specific about what they said or did",
            "- Acknowledge the effort but point out gaps if obvious",
            "- Reference past conversations and running jokes when relevant",
            "",
            "**What NOT to do:**",
            "- Generic responses (\"That's certainly a thing you said\")",
            "- Forced templates or prefixes",
            "- Sarcasm without grounding in actual behavior",
            "- Pretending you don't understand when you do",
            "",
            "**Response Length:**",
            "Keep it SHORT - 1-2 sentences max.",
            "",
            "**Tone:**",
            "Friendly but honest. Like a colleague who respects the work but won't sugarcoat problems.",
            "",
        ]


def extract_participant_profiles(user_conversations: Dict) -> Dict:
    """Extract participant profiles from conversation history."""
    profiles = {}

    for user_id, conversations in user_conversations.items():
        if not conversations:
            continue

        patterns = []
        topics = {}
        message_count = len(conversations)

        # Analyze messages for patterns
        for conv in conversations[-20:]:
            msg = conv.get("user_message", "").lower()

            if "onedrive" in msg:
                topics["OneDrive issues"] = topics.get("OneDrive issues", 0) + 1
            if "subprocess" in msg or "event loop" in msg:
                topics["Subprocess problems"] = topics.get("Subprocess problems", 0) + 1
            if "test" in msg:
                topics["Testing"] = topics.get("Testing", 0) + 1

        # Build patterns list
        if topics:
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
            patterns = [f"Often talks about: {topic}" for topic, _ in sorted_topics[:3]]

        profiles[user_id] = {
            "name": f"User {str(user_id)[:6]}",
            "message_count": message_count,
            "patterns": patterns,
        }

    return profiles

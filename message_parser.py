import json
from typing import Optional, Dict, Any, List

class MessageParser:
    """Parse Claude Code JSONL messages."""

    @staticmethod
    def parse_jsonl_line(line: str) -> Optional[Dict[str, Any]]:
        """Parse a single JSONL line."""
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError:
            return None

    @staticmethod
    def extract_assistant_message(parsed_json: Dict[str, Any]) -> Optional[str]:
        """
        Extract text response from assistant message.
        Returns: Combined text content from all text blocks.
        """
        if parsed_json.get("type") != "assistant":
            return None

        message = parsed_json.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            return None

        texts = []
        for block in content:
            if block.get("type") == "text":
                texts.append(block.get("text", ""))

        return "\n".join(texts) if texts else None

    @staticmethod
    def extract_tool_call(parsed_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract tool call information from message.
        Returns: {tool_name, tool_input_summary}
        """
        if parsed_json.get("type") != "assistant":
            return None

        message = parsed_json.get("message", {})
        content = message.get("content", [])

        if not isinstance(content, list):
            return None

        for block in content:
            if block.get("type") == "tool_use":
                return {
                    "tool_name": block.get("name"),
                    "tool_id": block.get("id"),
                    "tool_input": block.get("input"),
                }

        return None

    @staticmethod
    def build_action_context(parsed_json: Dict[str, Any]) -> str:
        """
        Build a context string describing what Claude just did.
        Used for sarcasm generation.
        """
        message = parsed_json.get("message", {})
        content = message.get("content", [])

        actions = []

        for block in content:
            if block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    actions.append(f"Responded: {text[:100]}...")

            elif block.get("type") == "tool_use":
                tool_name = block.get("name", "Unknown")
                actions.append(f"Called tool: {tool_name}")

        return " → ".join(actions) if actions else "Did something"

    @staticmethod
    def read_session_file(jsonl_path: str, start_line: int = 0) -> List[Dict[str, Any]]:
        """
        Read all new lines from session file starting from start_line.
        Returns list of parsed messages.
        """
        messages = []
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= start_line:
                        parsed = MessageParser.parse_jsonl_line(line)
                        if parsed:
                            messages.append(parsed)
        except Exception as e:
            print(f"Error reading session file: {e}")

        return messages

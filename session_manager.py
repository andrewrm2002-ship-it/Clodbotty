import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

class SessionManager:
    """Manages Claude Code sessions and auto-detects active session."""

    def __init__(self):
        self.projects_dir = Path.home() / ".claude" / "projects"
        self.user_sessions: Dict[int, Dict[str, Any]] = {}  # telegram_user_id -> session info

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """
        Auto-detect the most recently modified Claude Code session.
        Returns: {sessionId, projectPath, memoryPath, last_uuid, lastModified}
        """
        if not self.projects_dir.exists():
            return None

        most_recent = None
        most_recent_time = 0

        # Scan all .jsonl files in subagents directories
        try:
            for jsonl_file in self.projects_dir.glob("**/subagents/*.jsonl"):
                mod_time = os.path.getmtime(jsonl_file)

                if mod_time > most_recent_time:
                    most_recent_time = mod_time
                    project_path = jsonl_file.parent.parent.parent
                    memory_path = project_path / "memory" / "MEMORY.md"

                    most_recent = {
                        "sessionId": jsonl_file.stem,
                        "jsonlPath": str(jsonl_file),
                        "projectPath": str(project_path),
                        "memoryPath": str(memory_path) if memory_path.exists() else None,
                        "lastModified": datetime.fromtimestamp(mod_time).isoformat(),
                        "last_uuid": None,
                    }
        except Exception as e:
            print(f"Error scanning projects: {e}")
            return None

        return most_recent

    def get_memory_context(self, session: Dict[str, Any]) -> str:
        """
        Load MEMORY.md for context-aware sarcasm.
        Returns first 1000 chars for quick context.
        """
        if not session or not session.get("memoryPath"):
            return ""

        try:
            memory_file = Path(session["memoryPath"])
            if memory_file.exists():
                with open(memory_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Return first 500 chars for context
                    return content[:500]
        except Exception as e:
            print(f"Error reading memory: {e}")

        return ""

    def set_user_session(self, telegram_user_id: int, session: Dict[str, Any]):
        """Store session mapping for a Telegram user."""
        self.user_sessions[telegram_user_id] = session

    def get_user_session(self, telegram_user_id: int) -> Optional[Dict[str, Any]]:
        """Get session for a specific Telegram user."""
        return self.user_sessions.get(telegram_user_id)

    def initialize_user(self, telegram_user_id: int) -> Dict[str, Any]:
        """Initialize a new user with active session."""
        active_session = self.get_active_session()
        if active_session:
            self.set_user_session(telegram_user_id, active_session)
        return active_session

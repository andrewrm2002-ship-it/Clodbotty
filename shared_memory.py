import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class SharedMemory:
    """Manage shared memory across all chats and users for comic relief."""

    def __init__(self, memory_file: str = "shared_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict:
        """Load shared memory from file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading memory: {e}")
                return self._default_memory()
        return self._default_memory()

    def _default_memory(self) -> Dict:
        """Return default memory structure."""
        return {
            "funny_moments": [],  # List of memorable/funny interactions
            "running_jokes": [],  # Recurring jokes or patterns
            "observations": [],   # Bot's observations about users/patterns
            "roast_history": [],  # Recent roasts for variation
        }

    def _save_memory(self):
        """Save memory to file."""
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def add_funny_moment(self, description: str, user_id: int = None, chat_type: str = "unknown"):
        """Record a funny moment for later reference."""
        moment = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "user_id": user_id,
            "chat_type": chat_type,
        }
        self.memory["funny_moments"].append(moment)

        # Keep only last 50
        if len(self.memory["funny_moments"]) > 50:
            self.memory["funny_moments"] = self.memory["funny_moments"][-50:]

        self._save_memory()

    def add_running_joke(self, joke: str, trigger_pattern: str = None):
        """Add a running joke that gets referenced."""
        if joke not in [j["joke"] for j in self.memory["running_jokes"]]:
            self.memory["running_jokes"].append({
                "joke": joke,
                "trigger_pattern": trigger_pattern,
                "count": 0,
            })
            self._save_memory()

    def increment_joke_count(self, joke: str):
        """Track how many times a joke has been used."""
        for j in self.memory["running_jokes"]:
            if j["joke"] == joke:
                j["count"] += 1
                self._save_memory()
                break

    def get_running_jokes(self) -> List[str]:
        """Get list of running jokes."""
        return [j["joke"] for j in self.memory["running_jokes"]]

    def get_funny_moments(self, limit: int = 10) -> List[Dict]:
        """Get recent funny moments for context."""
        return self.memory["funny_moments"][-limit:]

    def add_observation(self, observation: str):
        """Add a general observation about patterns."""
        if observation not in [o["text"] for o in self.memory["observations"]]:
            self.memory["observations"].append({
                "timestamp": datetime.now().isoformat(),
                "text": observation,
            })

            # Keep only last 30
            if len(self.memory["observations"]) > 30:
                self.memory["observations"] = self.memory["observations"][-30:]

            self._save_memory()

    def get_observations(self) -> List[str]:
        """Get recent observations."""
        return [o["text"] for o in self.memory["observations"][-5:]]

    def get_memory_context(self) -> str:
        """Get formatted memory context for humor injection."""
        context_lines = []

        # Recent funny moments
        funny = self.get_funny_moments(3)
        if funny:
            context_lines.append("Recent moments:")
            for m in funny:
                context_lines.append(f"  - {m['description']}")

        # Running jokes
        jokes = self.get_running_jokes()
        if jokes:
            context_lines.append("\nRunning jokes:")
            for j in jokes[:3]:
                context_lines.append(f"  - {j}")

        # Observations
        obs = self.get_observations()
        if obs:
            context_lines.append("\nPatterns:")
            for o in obs[:2]:
                context_lines.append(f"  - {o}")

        return "\n".join(context_lines) if context_lines else ""

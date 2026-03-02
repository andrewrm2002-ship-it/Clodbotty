import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class UserManager:
    """Manage user profiles and conversation history."""

    def __init__(self, data_dir: str = "user_data"):
        self.data_dir = Path(data_dir)
        self.profiles_file = self.data_dir / "profiles.json"
        self.conversations_dir = self.data_dir / "conversations"

        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.conversations_dir.mkdir(exist_ok=True)

        self.profiles = self._load_profiles()

    def _load_profiles(self) -> Dict:
        """Load user profiles from file."""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading profiles: {e}")
                return {}
        return {}

    def _save_profiles(self):
        """Save profiles to file."""
        try:
            with open(self.profiles_file, "w") as f:
                json.dump(self.profiles, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")

    def get_or_create_profile(self, user_id: int) -> Dict:
        """Get user profile or create default one."""
        user_id_str = str(user_id)

        if user_id_str not in self.profiles:
            self.profiles[user_id_str] = {
                "user_id": user_id,
                "roast_level": "heavy",  # light, medium, heavy (HEAVY by default for max comedy)
                "created_at": datetime.now().isoformat(),
                "preferences": {},
            }
            self._save_profiles()

        return self.profiles[user_id_str]

    def set_roast_level(self, user_id: int, level: str) -> bool:
        """Set roast level (light, medium, heavy)."""
        if level not in ["light", "medium", "heavy"]:
            return False

        profile = self.get_or_create_profile(user_id)
        profile["roast_level"] = level
        self._save_profiles()
        return True

    def get_roast_level(self, user_id: int) -> str:
        """Get user's roast level."""
        profile = self.get_or_create_profile(user_id)
        return profile.get("roast_level", "heavy")

    def save_conversation(self, user_id: int, message: str, response: str):
        """Save user message and bot response."""
        conv_file = self.conversations_dir / f"{user_id}.json"

        try:
            conversations = []
            if conv_file.exists():
                with open(conv_file, "r") as f:
                    conversations = json.load(f)

            conversations.append({
                "timestamp": datetime.now().isoformat(),
                "user_message": message,
                "bot_response": response,
            })

            with open(conv_file, "w") as f:
                json.dump(conversations, f, indent=2)
        except Exception as e:
            print(f"Error saving conversation: {e}")

    def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's conversation history."""
        conv_file = self.conversations_dir / f"{user_id}.json"

        if not conv_file.exists():
            return []

        try:
            with open(conv_file, "r") as f:
                conversations = json.load(f)
                return conversations[-limit:]  # Return last N conversations
        except Exception as e:
            print(f"Error loading conversation history: {e}")
            return []

    def get_profile_info(self, user_id: int) -> str:
        """Get formatted profile info."""
        profile = self.get_or_create_profile(user_id)
        conv_count = len(self.get_conversation_history(user_id, limit=1000))

        return (
            f"🤖 **Your Profile**\n\n"
            f"Roast Level: {profile['roast_level'].upper()}\n"
            f"Conversations: {conv_count}\n"
            f"Member Since: {profile['created_at'][:10]}"
        )

import subprocess
import os
from typing import Optional, Tuple


class InputHandler:
    """Send prompts to Claude via CLI (uses existing Claude Pro subscription)."""

    def __init__(self, timeout: int = 30):
        """
        Initialize the input handler with Claude CLI.

        Args:
            timeout: Timeout in seconds for Claude responses
        """
        self.timeout = timeout

    def send_to_claude(
        self, message: str, session_info: dict = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Send message to Claude via `claude --print` CLI.

        Uses your existing Claude CLI and Pro subscription login.
        No API key needed - zero extra billing.

        Args:
            message: Prompt to send to Claude
            session_info: Unused (kept for compatibility)

        Returns:
            (response_text, error_message) - one will be None
        """
        if not message:
            return None, "Empty message"

        try:
            # Call Claude CLI directly
            # This uses your Pro subscription login stored locally
            result = subprocess.run(
                ["claude", "--print"],
                input=message,
                capture_output=True,
                timeout=self.timeout,
                text=True,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                print(f"[Claude CLI Error] Return code {result.returncode}: {error_msg[:200]}")
                return None, f"Claude error: {error_msg[:100]}"

            # Claude --print returns response in stdout
            if result.stdout and result.stdout.strip():
                return result.stdout.strip(), None
            else:
                return None, "Claude returned empty response"

        except subprocess.TimeoutExpired:
            return None, f"Claude timeout (>{self.timeout}s)"
        except FileNotFoundError:
            return None, "Claude CLI not found. Make sure 'claude' is installed and in PATH."
        except Exception as e:
            error_msg = str(e)
            print(f"[Claude CLI Exception] {error_msg[:200]}")
            return None, f"Error: {error_msg[:100]}"

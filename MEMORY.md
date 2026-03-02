# Clodbotty Bot - Project Memory

## Project Overview

**Clodbotty** is a Telegram bot that responds to messages in friend group chats with honest, contextual humor. Instead of forced sarcasm, it finds genuine opportunities to be funny while remaining helpful and self-aware.

**Key Philosophy (Updated Mar 1, 2026):** Honest first, humor when genuine. Smart, not forced.

## Core Architecture

### Main Bot (bot.py)
- Entry point for all Telegram message handling
- Uses `python-telegram-bot` library
- Initializes managers: SessionManager, InputHandler, Roaster, UserManager, SharedMemory, ClaudeMDUpdater
- Key handler: `handle_message()` which:
  1. Loads conversation history (user messages only - not bot responses)
  2. Gets shared memory context (running jokes, patterns)
  3. Calls `roaster.roast_with_context()` to invoke Claude LLM
  4. Saves response to history
  5. Updates CLAUDE.md with live context
  6. Sends response to Telegram

### Response Generation (roaster.py)
- Generates responses by calling Claude LLM directly
- `roast_with_context()` async method:
  - Builds prompt with full context
  - Calls `input_handler.send_to_claude(prompt, session)` to invoke Claude
  - Returns Claude's response
- Prompt includes:
  - Instructions: Be honest, find natural humor, know when to be silent
  - User's conversation history (last 10 user messages only)
  - Shared memory (running jokes, patterns, observations)
  - Known patterns about the user

### Context Management (claude_md_updater.py)
- Dynamically updates CLAUDE.md after each message
- Extracts and tracks:
  - Running jokes with usage counts
  - Recent funny moments (last 10)
  - Conversation patterns (what topics are discussed)
  - Participant profiles and their patterns
  - Observations about behavior
- Writes to: `C:\Users\andre\OneDrive\Desktop\Clodbotty_bot\CLAUDE.md`

### Memory Systems

**Shared Memory (shared_memory.py + shared_memory.json)**
- Cross-chat memory persisting across all conversations
- Tracks funny moments, running jokes, observations
- Gets passed to Claude for contextual understanding
- Pre-loaded with Andrew's patterns (OneDrive issues, subprocess problems, test-once behavior)

**User Manager (user_manager.py)**
- Per-user conversation history and profiles
- Stores in: `user_data/conversations/{user_id}.json`
- Default roast_level: "heavy" (no longer used - LLM determines responses)

### Session & Input Handling

**SessionManager (session_manager.py)**
- Detects active Claude Code session for `/ask` command
- Tracks session metadata

**InputHandler (input_handler.py)**
- `send_to_claude(prompt, session)` invokes Claude via CLI
- Returns response from Claude

## Key Files

| File | Purpose |
|------|---------|
| `bot.py` | Main Telegram bot orchestrator |
| `roaster.py` | Response generation with Claude LLM |
| `claude_md_updater.py` | Dynamically updates CLAUDE.md |
| `shared_memory.py` | Tracks funny moments, jokes, observations |
| `user_manager.py` | Per-user conversation history |
| `session_manager.py` | Claude Code session detection |
| `input_handler.py` | Claude invocation wrapper |
| `CLAUDE.md` | Auto-updated context file (read by bot) |
| `shared_memory.json` | Persistent memory storage |
| `user_data/` | Per-user conversation history |

## Recent Changes (Mar 1, 2026)

### Personality Shift: "Honest First, Humor When Genuine"

**What Changed:**
- From: "Be sarcastic first, helpful second"
- To: "Be honest first, find natural humor opportunities"

**Updated In:**
1. `roaster.py` - Prompt instructions rewritten
2. `README.md` - Philosophy and features updated
3. Code consolidation - Moved CLAUDE.md from ~/.claude/projects to bot directory

**Key Guidelines Now:**
- Only be sarcastic or joke when it's TRULY funny, not forced
- Know when to be silent - silence is better than filler
- Never respond just to respond
- Find original observations based on patterns
- Self-deprecation works when genuine

## Bot Response Flow

```
User sends Telegram message
    ↓
bot.handle_message()
    ├─ Load conversation history (last 10 user messages)
    ├─ Load shared memory (running jokes, patterns)
    ├─ Build prompt with all context
    ├─ Call roaster.roast_with_context()
    │   ├─ Send prompt to Claude via input_handler
    │   └─ Return Claude's response
    ├─ Save to conversation history
    ├─ Update CLAUDE.md via ClaudeMDUpdater
    └─ Send response to Telegram
```

## Andrew's Known Patterns

These are tracked in shared_memory.json and referenced when relevant:
- OneDrive storage issues on Windows (recurring problem)
- Subprocess/event loop problems (Windows-specific nightmares)
- Tests code once, confident it works, breaks elsewhere
- Builds experimental bots (Clodbotty is one of them!)

## Configuration

**.env file:**
```
TELEGRAM_BOT_TOKEN=<your_token>
```

**Dependencies:**
- python-telegram-bot==21.0.1
- watchdog==4.0.0
- python-dotenv==1.0.1

## Important Commands

- `/start` - Bot info
- `/ask <question>` - Explicit Claude help
- `/memory` - View shared memory
- `/history` - User's recent conversations
- `/profile` - User profile info
- Any message → Bot responds contextually

## Development Notes

### Why This Architecture?
1. **No API costs** - Uses local Claude Code session (Pro subscription)
2. **Full context** - Bot understands entire conversation history
3. **Smart responses** - Claude generates responses, not templates
4. **Memory persistence** - Learns patterns over time
5. **Easy to extend** - Modular design makes adding features simple

### Common Issues & Solutions

**Bot says "Okay" to everything:**
- Claude Code session not running
- Fix: Start Claude in terminal with `claude`

**Bot responds with templated humor:**
- Check roaster.py is calling Claude LLM
- Verify input_handler.send_to_claude() is being invoked

**CLAUDE.md not updating:**
- Check claude_md_updater.py path is correct
- Verify bot has write permissions to Desktop folder

## Session File Format (Reference)

Claude Code writes to `.jsonl` files with format:
```json
{
  "type": "assistant|user|progress",
  "message": {
    "content": [
      {"type": "text", "text": "..."},
      {"type": "tool_use", "name": "Bash", "input": {...}}
    ]
  }
}
```

## Current Status

✅ Bot is running with new "honest first" philosophy
✅ All files consolidated to Desktop/Clodbotty_bot
✅ CLAUDE.md auto-updates with live context
✅ Responses generated by Claude LLM (not templates)
✅ Shared memory tracking running jokes and patterns
✅ Conversation history per user maintained

---

Last Updated: 2026-03-01
Philosophy: Honest first, humor when genuine, smart not forced
Status: Active and learning from conversations

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from session_manager import SessionManager
from input_handler import InputHandler
from roaster import Roaster
from message_parser import MessageParser
from user_manager import UserManager
from shared_memory import SharedMemory
from claude_md_updater import ClaudeMDUpdater, extract_participant_profiles

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize managers
session_manager = SessionManager()
input_handler = InputHandler()
roaster = Roaster()
user_manager = UserManager()
shared_memory = SharedMemory()
claude_md_updater = ClaudeMDUpdater()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /start command."""
    user_id = update.effective_user.id
    user_manager.get_or_create_profile(user_id)

    await update.message.reply_text(
        "🤖 **Clodbotty** — Your sarcastic Telegram companion.\n\n"
        "I remember everything you say across all chats. My job is to roast you relentlessly.\n\n"
        "Send me anything and I'll respond with maximum sass. Self-deprecation included.\n\n"
        "**Commands:**\n"
        "• `/memory` - The roasts I remember\n"
        "• `/ask <question>` - Get actual Claude help (boring mode)\n"
        "• `/history` - Your past embarrassments\n\n"
        "Otherwise: just chat. I'm always watching. 👀"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for user messages - honest, direct responses using Claude."""
    user_id = update.effective_user.id
    user_message = update.message.text
    chat_type = update.effective_chat.type

    logger.info(f"📨 Message | User: {user_id} | Chat: {chat_type} | Text: {user_message[:50]}")

    try:
        # Get session (optional - if no Claude Code running, bot falls back gracefully)
        session = session_manager.get_user_session(user_id)
        if not session:
            session = session_manager.initialize_user(user_id)

        # Show typing indicator
        await update.message.chat.send_action("typing")

        # Get context
        shared_memory_context = shared_memory.get_memory_context()
        conversation_history = user_manager.get_conversation_history(user_id, limit=10)

        logger.info(f"Session available: {session is not None}")
        logger.info(f"Conversation history: {len(conversation_history) if conversation_history else 0} items")

        # Generate response using Claude with full context
        response, error = await roaster.roast_with_context(
            user_message=user_message,
            user_id=user_id,
            session=session,
            shared_memory_context=shared_memory_context,
            conversation_history=conversation_history,
            input_handler=input_handler,
        )

        logger.info(f"Response: {response}, Error: {error}")

        if error:
            logger.error(f"Roaster error: {error}")
            # Fallback to simple acknowledgment if Claude fails
            response = "Got it."

        if not response:
            logger.warning(f"Empty response from roaster")
            response = "Got it."

        # Record what they said (for patterns/learning)
        shared_memory.add_funny_moment(
            f"Someone said: '{user_message[:50]}'",
            user_id=user_id,
            chat_type=chat_type
        )

        # Save to conversation history
        user_manager.save_conversation(user_id, user_message, response)

        # Update CLAUDE.md with live context for future responses
        try:
            all_conversations = {}
            # Gather all user conversations for context
            for uid in [user_id]:  # Can expand to gather from multiple users
                hist = user_manager.get_conversation_history(uid, limit=50)
                if hist:
                    all_conversations[uid] = hist

            participant_profiles = extract_participant_profiles(all_conversations)
            recent_convs = all_conversations.get(user_id, [])[-10:]

            claude_md_updater.update_with_context(
                shared_memory=shared_memory.memory,
                participant_profiles=participant_profiles,
                recent_conversations=recent_convs,
            )
            logger.info("✅ Updated CLAUDE.md with live context")
        except Exception as e:
            logger.warning(f"Could not update CLAUDE.md: {e}")

        # Send the response
        await update.message.reply_text(response, parse_mode=None)

        logger.info("Response sent successfully")

    except Exception as e:
        logger.error(f"Error responding: {e}")
        await update.message.reply_text(f"Something broke: {str(e)[:100]}")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /status command."""
    user_id = update.effective_user.id

    session = session_manager.get_user_session(user_id)
    if not session:
        session = session_manager.get_active_session()

    if session:
        await update.message.reply_text(
            f"✅ Active session found:\n"
            f"ID: {session['sessionId']}\n"
            f"Project: {session['projectPath']}\n"
            f"Last modified: {session['lastModified']}"
        )
    else:
        await update.message.reply_text("❌ No active Claude Code session detected.")


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /profile command."""
    user_id = update.effective_user.id
    user_manager.get_or_create_profile(user_id)
    profile_info = user_manager.get_profile_info(user_id)
    await update.message.reply_text(profile_info)


async def roast_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /roast_level command (deprecated - replaced with context-aware responses)."""
    await update.message.reply_text(
        "The roast level system is gone. 🎯\n\n"
        "Clodbotty now responds based on actual context, not intensity levels.\n\n"
        "Your responses depend on:\n"
        "• What you actually said\n"
        "• What patterns I've learned about you\n"
        "• Whether I have something real to respond with\n\n"
        "No templates. No forced sass. Just honest feedback."
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /history command."""
    user_id = update.effective_user.id
    conversations = user_manager.get_conversation_history(user_id, limit=5)

    if not conversations:
        await update.message.reply_text("📭 No conversation history yet.")
        return

    history_text = "📜 **Recent Conversations** (Last 5):\n\n"
    for i, conv in enumerate(conversations, 1):
        timestamp = conv["timestamp"][:16]  # YYYY-MM-DD HH:MM
        user_msg = conv["user_message"][:30]
        bot_response = conv["bot_response"][:40]
        history_text += (
            f"{i}. **[{timestamp}]**\n"
            f"   You: {user_msg}...\n"
            f"   Bot: {bot_response}...\n\n"
        )

    await update.message.reply_text(history_text)


async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /debug command - diagnose issues."""
    user_id = update.effective_user.id

    # Check session
    session = session_manager.get_user_session(user_id)
    if not session:
        session = session_manager.initialize_user(user_id)

    status_lines = [
        "🔍 **Clodbotty Diagnostics**\n",
    ]

    if session:
        status_lines.append(f"✅ Claude Code session found: {session.get('sessionId', 'unknown')}")
    else:
        status_lines.append("❌ No Claude Code session - is `claude` running in another terminal?")

    # Check conversation history
    history = user_manager.get_conversation_history(user_id, limit=10)
    status_lines.append(f"📝 Conversation history: {len(history)} messages")

    # Check shared memory
    memory_context = shared_memory.get_memory_context()
    if memory_context:
        status_lines.append(f"💭 Shared memory: {len(memory_context)} chars")
    else:
        status_lines.append("💭 Shared memory: Empty (will fill over time)")

    status_lines.append("\n**To fix 'Okay' responses:**")
    status_lines.append("1. Open a terminal and run: `claude`")
    status_lines.append("2. Keep it open while using the bot")
    status_lines.append("3. Send a test message to the bot")
    status_lines.append("4. Check the bot logs for errors")

    await update.message.reply_text("\n".join(status_lines))


async def memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /memory command - view shared memory."""
    memory_text = "🧠 **My Memory Across All Chats**\n\n"

    # Show funny moments
    funny_moments = shared_memory.get_funny_moments(5)
    if funny_moments:
        memory_text += "**Recent Funny Moments:**\n"
        for m in funny_moments:
            memory_text += f"  • {m['description']}\n"
        memory_text += "\n"

    # Show running jokes
    jokes = shared_memory.get_running_jokes()
    if jokes:
        memory_text += "**Running Jokes:**\n"
        for j in jokes[:5]:
            memory_text += f"  • {j}\n"
        memory_text += "\n"

    # Show observations
    obs = shared_memory.get_observations()
    if obs:
        memory_text += "**Observations:**\n"
        for o in obs:
            memory_text += f"  • {o}\n"

    if not funny_moments and not jokes and not obs:
        memory_text += "_Nothing yet. Go forth and be hilarious._"

    await update.message.reply_text(memory_text)


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /ask command - explicitly invoke Claude for help."""
    user_id = update.effective_user.id

    # Get the question from args
    if not context.args:
        await update.message.reply_text(
            "Usage: `/ask <question>`\n\n"
            "Example: `/ask how do I sort a list in Python`"
        )
        return

    question = " ".join(context.args)

    # Initialize session if needed
    session = session_manager.get_user_session(user_id)
    if not session:
        session = session_manager.initialize_user(user_id)

    if not session:
        await update.message.reply_text(
            "❌ No Claude Code session detected.\n"
            "Start Claude Code first: `claude`"
        )
        return

    # Show typing indicator
    await update.message.chat.send_action("typing")

    try:
        logger.info(f"Explicit ask from {user_id}: {question[:50]}...")

        # Send to Claude
        response, error = input_handler.send_to_claude(question, session)

        if error:
            logger.error(f"Claude error: {error}")
            await update.message.reply_text(f"⚠️ Claude couldn't help: {error}")
            return

        if not response:
            await update.message.reply_text("❌ No response from Claude.")
            return

        # Save to history
        user_manager.save_conversation(user_id, question, response)

        # Send response (brief, no extra commentary needed)
        if len(response) > 4096:
            await update.message.reply_text(response[:4090], parse_mode=None)
        else:
            await update.message.reply_text(response, parse_mode=None)

        logger.info("Claude response sent successfully")

    except Exception as e:
        logger.error(f"Error asking Claude: {e}")
        await update.message.reply_text(f"💥 Something went wrong: {str(e)[:100]}")


def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file!")

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(CommandHandler("debug", debug))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("roast_level", roast_level))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(CommandHandler("memory", memory))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start polling
    logger.info("🤖 Clodbotty starting...")
    logger.info("✅ Handlers registered. Listening for messages...")
    logger.info("⚠️  DEBUG: If you send messages and don't see '📨 MESSAGE RECEIVED', privacy mode is ON")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        main()
    finally:
        loop.close()

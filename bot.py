from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
from start import setup_start_handlers
from profile import setup_profile_handlers
from discovery import setup_discovery_handlers
from matching import setup_matching_handlers, setup_match_command
from database import users

app = Client(
    "dating_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workdir="/content" if __import__("os").path.exists("/content") else ".",
)


@app.on_message(filters.command("help") & filters.private)
async def cmd_help(client, message):
    from database import get_user
    from languages import t
    u = get_user(message.from_user.id) or {}
    lang = u.get("language", "en")
    await message.reply_text(t(lang, "help"))


@app.on_message(filters.command("delete") & filters.private)
async def cmd_delete(client, message):
    from database import delete_user, get_user
    from languages import t
    u = get_user(message.from_user.id) or {}
    lang = u.get("language", "en")
    delete_user(message.from_user.id)
    await message.reply_text(t(lang, "profile_deleted"))


def main():
    # Order matters — command handlers first, then generic message handler
    setup_start_handlers(app)
    setup_discovery_handlers(app)
    setup_matching_handlers(app)
    setup_match_command(app)
    setup_profile_handlers(app)   # ← generic handler must be last

    print("🤖 Dating Bot is starting...")
    app.run()


if __name__ == "__main__":
    main()

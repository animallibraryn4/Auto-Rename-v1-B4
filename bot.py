import sys
import os

# Check if required packages are installed
try:
    from pyrogram import Client
except ImportError as e:
    print("❌ Pyrogram not found. Installing required packages...")
    os.system(f"{sys.executable} -m pip install pyrogram==2.0.80 TgCrypto motor dnspython")
    print("✅ Packages installed. Please restart the bot.")
    sys.exit(1)

# Now import the rest
from plugins.file_rename import queue_manager
import aiohttp, asyncio, warnings, pytz
from datetime import datetime, timedelta
from pytz import timezone
from pyrogram import Client
from config import Config
from aiohttp import web
from route import web_server
import pyrogram.utils
import pyromod
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import time

# Try to import libtorrent, but don't fail if it's missing
try:
    import libtorrent as lt
    LIBTORRENT_AVAILABLE = True
    print("✅ libtorrent is available")
except ImportError:
    LIBTORRENT_AVAILABLE = False
    print("⚠ libtorrent is not available. Torrent features will be disabled.")

pyrogram.utils.MIN_CHANNEL_ID = -1001896877147

SUPPORT_CHAT = int(os.environ.get("SUPPORT_CHAT", "-1001896877147"))

# global bot instance for ban system
bot = None

class Bot(Client):
    def __init__(self):
        global bot
        super().__init__(
            name="N4_BOTS",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            in_memory=True,
            workers=50,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )
        bot = self  # Set global bot instance
        self.start_time = time.time()

    async def start(self):
        await super().start()

        me = await self.get_me()
        print(f"{me.first_name} Is Started.....😊")
        # Initialize queue manager with client
        queue_manager.set_client(self)
        
        self.start_time = time.time()

        uptime_seconds = int(time.time() - self.start_time)
        uptime_string = str(timedelta(seconds=uptime_seconds))

        for chat_id in [Config.LOG_CHANNEL, SUPPORT_CHAT]:
            try:
                await self.send_photo(
                    chat_id=chat_id,
                    photo=Config.START_PIC,
                    caption=(
                        f"**{me.first_name} Is Restarted Again!**\n\n"
                        f"System Uptime` {uptime_string}`."
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton(
                                "ᴜᴘᴅᴀᴛᴇs",
                                url="https://t.me/animelibraryn4"
                            )
                        ]]
                    )
                )
            except Exception as e:
                print(e)

if __name__ == "__main__":
    print("=" * 50)
    print("Starting Auto-Rename Bot with Torrent Support")
    print("=" * 50)
    
    if not LIBTORRENT_AVAILABLE:
        print("⚠ Warning: libtorrent is not installed.")
        print("Torrent features will be disabled.")
        print("To enable torrent features, install libtorrent:")
        print("sudo apt-get install python3-libtorrent")
        print("or")
        print("pip install libtorrent==2.0.9")
        print("=" * 50)
    
    # Check if config is set
    if not Config.API_ID or not Config.API_HASH or not Config.BOT_TOKEN:
        print("❌ Error: API_ID, API_HASH, or BOT_TOKEN not set in config!")
        print("Please set these environment variables:")
        print("export API_ID='your_api_id'")
        print("export API_HASH='your_api_hash'")
        print("export BOT_TOKEN='your_bot_token'")
        sys.exit(1)
    
    print("✅ Bot configuration loaded successfully")
    print("Starting bot...")
    
    try:
        Bot().run()
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("Please check your configuration and try again.")

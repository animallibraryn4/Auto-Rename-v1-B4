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

    # Add at the end of Bot class or in cleanup function
    async def stop(self):
        await bypasser.close_session()
        await super().stop()

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
    Bot().run()

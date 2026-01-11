
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

class FileRouter:
    def __init__(self):
        self.processing_lock = {}  # user_id -> lock
        
    async def get_user_lock(self, user_id):
        """Get or create lock for user to prevent duplicate processing"""
        if user_id not in self.processing_lock:
            self.processing_lock[user_id] = asyncio.Lock()
        return self.processing_lock[user_id]

    async def route_file(self, client: Client, message: Message):
        """Main routing logic - decides which handler to use"""
        user_id = message.from_user.id
        text = message.text or message.caption or ""

        # 1. Check if user is banned
        from plugins.admin_panel import is_user_banned
        if await is_user_banned(user_id):
            return True

        # 2. Handle Commands
        if text.startswith("/"):
            cmd_args = text.split()
            message.command = cmd_args # Fixes 'NoneType' len() error
            command = cmd_args[0].lower()
            
            # If it's an Admin command, handle it here
            if user_id in Config.ADMIN:
                from plugins.admin_panel import (
                    restart_bot, get_stats, broadcast_handler, 
                    ban_command, unban_command, tban_command, banlist_command
                )

                if command == "/restart":
                    await restart_bot(client, message)
                    return True
                elif command in ["/stats", "/status"]:
                    await get_stats(client, message)
                    return True
                elif command == "/broadcast":
                    await broadcast_handler(client, message)
                    return True
                elif command == "/ban":
                    await ban_command(client, message)
                    return True
            
            # 3. ALLOW USER COMMANDS TO PASS THROUGH
            # List commands that should be handled by other files (start.py, metadata.py, etc.)
            public_commands = ["/start", "/help", "/mode", "/metadata", "/tutorial", "/donate"]
            if command in public_commands:
                return False # This lets Pyrogram look for other handlers

        # 4. Filter for actual media
        # Prevent plain text (that isn't a command) from being sent to the renamer
        if not (message.document or message.video or message.audio):
            return False

        # Get lock for this user to prevent concurrent file processing
        async with await self.get_user_lock(user_id):
            
            # 1. Check Info Mode (Highest Priority)
            from plugins.auto_rename import info_mode_users
            if user_id in info_mode_users:
                from plugins.auto_rename import process_file_for_info
                await process_file_for_info(client, message)
                return True
            
            # 2. Check Sequence Mode
            from plugins.sequence import user_sequences
            if user_id in user_sequences:
                from plugins.sequence import store_file
                await store_file(client, message)
                return True
            
            # 3. Check Verification
            from plugins import is_user_verified, send_verification
            if not await is_user_verified(user_id):
                await send_verification(client, message)
                return True
            
            # 4. Default: Auto-Rename Mode
            from plugins.file_rename import process_rename
            await process_rename(client, message)
            return True

        if message.text and message.text.startswith("/start"):
            from plugins.start import start
            await start(client, message)
            return True
        
        return False

# Global router instance
file_router = FileRouter()

# Single handler for all files and text
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.text))
async def handle_everything(client, message):
    """Single entry point for the entire bot"""
    # Fix: ensure we call route_file, not route_message
    await file_router.route_file(client, message)





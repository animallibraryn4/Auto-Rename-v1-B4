
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
        text = message.text or message.caption or "" # Define text to avoid NameError

        # Check if user is banned first
        from plugins.admin_panel import is_user_banned
        if await is_user_banned(user_id):
            return True

        # Handle Admin Commands
        if text.startswith("/") and user_id in Config.ADMIN:
            cmd_args = text.split()
            message.command = cmd_args
            command = cmd_args[0].lower()
            
            # List of commands this router SHOULD handle
            admin_commands = ["/restart", "/stats", "/status", "/broadcast", "/ban", "/unban", "/tban", "/banlist"]
            
            if command in admin_commands:
                from plugins.admin_panel import (
                    restart_bot, get_stats, broadcast_handler, 
                    ban_command, unban_command, tban_command, banlist_command
                )
                if command == "/restart": await restart_bot(client, message)
                elif command in ["/stats", "/status"]: await get_stats(client, message)
                elif command == "/broadcast": await broadcast_handler(client, message)
                elif command == "/ban": await ban_command(client, message)
                elif command == "/unban": await unban_command(client, message)
                elif command == "/tban": await tban_command(client, message)
                elif command == "/banlist": await banlist_command(client, message)
                return True # Stop here, command was handled

        # 2. NEW: Ignore standard user commands so they reach start.py
        user_commands = ["/start", "/help", "/donate", "/tutorial", "/bought"]
        if text.split()[0].lower() in user_commands:
            return False # Returning False allows Pyrogram to look for other handlers (like in start.py)

        # 3. Only process if it's an actual file or if you intend to rename based on text
        if not (message.document or message.video or message.audio):
            return False # Ignore plain text that isn't a command or a file

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
        
        return False

# Global router instance
file_router = FileRouter()

# Single handler for all files and text
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.text))
async def handle_everything(client, message):
    """Single entry point for the entire bot"""
    # Fix: ensure we call route_file, not route_message
    await file_router.route_file(client, message)

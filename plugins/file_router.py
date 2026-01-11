import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

class FileRouter:
    def __init__(self):
        self.processing_lock = {}  # user_id -> lock
        
    async def get_user_lock(self, user_id):
        if user_id not in self.processing_lock:
            self.processing_lock[user_id] = asyncio.Lock()
        return self.processing_lock[user_id]
    
    async def route_message(self, client: Client, message: Message):
        """Main routing logic - handles both Commands and Files"""
        user_id = message.from_user.id
        text = message.text or ""
        
        # 1. Handle Admin Commands (Highest Priority)
        # This replaces the @Client.on_message(filters.command("vpanel")) in vpanel.py
        if text.startswith("/") and user_id in Config.ADMIN:
            if text.split()[0] == "/vpanel":
                from plugins.vpanel import vpanel_command
                await vpanel_command(client, message)
                return True
            # Add other admin commands here (e.g., /stats) if needed

        # 2. Handle File Processing (Locks used here to prevent spam)
        if message.document or message.video or message.audio:
            async with await self.get_user_lock(user_id):
                
                # A. Check Info Mode
                from plugins.auto_rename import info_mode_users
                if user_id in info_mode_users:
                    from plugins.auto_rename import process_file_for_info
                    await process_file_for_info(client, message)
                    return True
                
                # B. Check Sequence Mode
                from plugins.sequence import user_sequences
                if user_id in user_sequences:
                    from plugins.sequence import store_file
                    await store_file(client, message)
                    return True
                
                # C. Check Verification
                from plugins import is_user_verified, send_verification
                if not await is_user_verified(user_id):
                    await send_verification(client, message)
                    return True
                
                # D. Default: Auto-Rename Mode
                from plugins.file_rename import process_rename
                await process_rename(client, message)
                return True
        
        return False

# Global router instance
file_router = FileRouter()

# UPDATED FILTER: Now listens for commands AND files
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.text))
async def handle_everything(client, message):
    """Single entry point for the entire bot"""
    await file_router.route_message(client, message)
    

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

from pyrogram import Client, filters
from pyrogram.types import Message
from plugins.admin_panel import check_and_notify_banned_user

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
        
        # Get lock for this user
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

# Single handler for all files
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_all_files(client, message):
    """Single entry point for all file processing"""
    await file_router.route_file(client, message)


# List of commands that should NOT be blocked for banned users
ALLOWED_COMMANDS_FOR_BANNED = ["start", "help"]

@Client.on_message(filters.private)
async def ban_middleware(client: Client, message: Message):
    """Middleware to check if user is banned before processing any command"""
    user_id = message.from_user.id
    
    # Check if message is a command
    if message.text and message.text.startswith('/'):
        # Extract command name (remove the / and any parameters)
        command_parts = message.text.split()
        if command_parts:
            command = command_parts[0][1:].lower()  # Remove / and convert to lowercase
            
            # Skip ban check for allowed commands
            if command in ALLOWED_COMMANDS_FOR_BANNED:
                return
            
            # Check if user is banned and notify them
            if await check_and_notify_banned_user(client, user_id):
                # Stop further processing of this command
                return True  # This will prevent other handlers from processing
    
    # For non-command messages (files, text, etc.)
    else:
        # Check if user is banned and notify them
        if await check_and_notify_banned_user(client, user_id):
            # Stop further processing
            return True
    
    # If not banned or command is allowed, continue processing
    return False

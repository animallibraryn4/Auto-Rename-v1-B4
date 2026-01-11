import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

class FileRouter:
    def __init__(self):
        self.processing_lock = {}  # user_id -> lock
        self.admin_commands = {
            # vpanel commands
            "vpanel": self.handle_vpanel,
            "add_premium": self.handle_add_premium,
            "remove_premium": self.handle_remove_premium,
            "set_expiry": self.handle_set_expiry,
            "set_shortlink": self.handle_set_shortlink,
            "set_tutorial": self.handle_set_tutorial,
            "set_image": self.handle_set_image,
            "set_api_key": self.handle_set_api_key,
            "test_vpanel": self.handle_test_vpanel,
            
            # admin_panel commands
            "restart": self.handle_restart,
            "tutorial": self.handle_tutorial,
            "stats": self.handle_stats,
            "status": self.handle_stats,  # Alias for stats
            "broadcast": self.handle_broadcast,
            "ban": self.handle_ban,
            "tban": self.handle_tban,
            "unban": self.handle_unban,
            "banlist": self.handle_banlist,
        }
        
    async def get_user_lock(self, user_id):
        """Get or create lock for user to prevent duplicate processing"""
        if user_id not in self.processing_lock:
            self.processing_lock[user_id] = asyncio.Lock()
        return self.processing_lock[user_id]
    
    # ========== ADMIN COMMAND HANDLERS ==========
    
    async def handle_vpanel(self, client: Client, message: Message):
        """Handle /vpanel command"""
        try:
            from plugins.vpanel import vpanel_command
            await vpanel_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_add_premium(self, client: Client, message: Message):
        """Handle /add_premium command"""
        try:
            from plugins.vpanel import handle_add_premium_command
            await handle_add_premium_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_remove_premium(self, client: Client, message: Message):
        """Handle /remove_premium command"""
        try:
            from plugins.vpanel import handle_remove_premium_command
            await handle_remove_premium_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_set_expiry(self, client: Client, message: Message):
        """Handle /set_expiry command"""
        try:
            from plugins.vpanel import set_expiry_command
            await set_expiry_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_set_shortlink(self, client: Client, message: Message):
        """Handle /set_shortlink command"""
        try:
            from plugins.vpanel import set_shortlink_command
            await set_shortlink_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_set_tutorial(self, client: Client, message: Message):
        """Handle /set_tutorial command"""
        try:
            from plugins.vpanel import set_tutorial_command
            await set_tutorial_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_set_image(self, client: Client, message: Message):
        """Handle /set_image command"""
        try:
            from plugins.vpanel import set_image_command
            await set_image_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_set_api_key(self, client: Client, message: Message):
        """Handle /set_api_key command"""
        try:
            from plugins.vpanel import set_api_key_command
            await set_api_key_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_test_vpanel(self, client: Client, message: Message):
        """Handle /test_vpanel command"""
        try:
            from plugins.vpanel import test_vpanel
            await test_vpanel(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_restart(self, client: Client, message: Message):
        """Handle /restart command"""
        try:
            from plugins.admin_panel import restart_bot
            await restart_bot(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_tutorial(self, client: Client, message: Message):
        """Handle /tutorial command"""
        try:
            from plugins.admin_panel import tutorial
            await tutorial(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_stats(self, client: Client, message: Message):
        """Handle /stats command"""
        try:
            from plugins.admin_panel import get_stats
            await get_stats(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_broadcast(self, client: Client, message: Message):
        """Handle /broadcast command"""
        try:
            from plugins.admin_panel import broadcast_handler
            await broadcast_handler(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_ban(self, client: Client, message: Message):
        """Handle /ban command"""
        try:
            from plugins.admin_panel import ban_command
            await ban_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_tban(self, client: Client, message: Message):
        """Handle /tban command"""
        try:
            from plugins.admin_panel import tban_command
            await tban_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_unban(self, client: Client, message: Message):
        """Handle /unban command"""
        try:
            from plugins.admin_panel import unban_command
            await unban_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_banlist(self, client: Client, message: Message):
        """Handle /banlist command"""
        try:
            from plugins.admin_panel import banlist_command
            await banlist_command(client, message)
        except Exception as e:
            await message.reply_text(f"❌ Error: {str(e)}")
    
    # ========== FILE PROCESSING ==========
    
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

# ========== IMPORTANT: KEEP BOTH HANDLERS ==========

# Handler 1: For normal user file processing (THIS MUST EXIST)
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_all_files(client, message):
    """Single entry point for all file processing"""
    await file_router.route_file(client, message)

# Handler 2: For admin commands only
@Client.on_message(filters.private & filters.incoming)
async def handle_all_messages(client, message):
    """Single entry point for ALL admin command processing"""
    # Route admin commands if user is admin
    if message.from_user.id in Config.ADMIN:
        await file_router.route_admin_command(client, message)

# ========== ADD THIS MISSING METHOD ==========

async def route_admin_command(self, client: Client, message: Message):
    """Route admin commands only"""
    user_id = message.from_user.id
    
    # Only process if user is admin
    if user_id not in Config.ADMIN:
        return False
    
    # Check if it's a command
    if message.text and message.text.startswith('/'):
        command_parts = message.text.split()
        if command_parts:
            command = command_parts[0][1:].lower()  # Remove leading '/'
            
            # Handle admin commands
            if command in self.admin_commands:
                await self.admin_commands[command](client, message)
                return True
    
    return False

# Add the method to the class
FileRouter.route_admin_command = route_admin_command

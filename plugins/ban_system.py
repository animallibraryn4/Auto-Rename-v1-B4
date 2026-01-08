from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import codeflixbots
from config import Config
import datetime

# =====================================================
# BAN CHECK MIDDLEWARE
# =====================================================

async def check_ban_middleware(client, message):
    """Middleware to check if user is banned"""
    user_id = message.from_user.id
    
    # Check if user is banned
    is_banned = await codeflixbots.is_user_banned(user_id)
    
    if is_banned:
        # Send ban message only once (prevent spam)
        if not hasattr(check_ban_middleware, "banned_notified"):
            check_ban_middleware.banned_notified = set()
        
        if user_id not in check_ban_middleware.banned_notified:
            check_ban_middleware.banned_notified.add(user_id)
            await message.reply_text(
                "🚫 **You are banned.**\n"
                "You are not allowed to use this bot anymore."
            )
        
        # Always return True to stop further processing
        return True
    
    # Clear from notified set if user was previously banned but now unbanned
    if hasattr(check_ban_middleware, "banned_notified"):
        check_ban_middleware.banned_notified.discard(user_id)
    
    return False

# =====================================================
# BAN COMMANDS (ADMIN ONLY)
# =====================================================

@Client.on_message(filters.private & filters.command("ban") & filters.user(Config.ADMIN))
async def ban_user_command(client: Client, message: Message):
    """Ban a user - Admin only"""
    if len(message.command) < 2:
        await message.reply_text(
            "**Usage:** `/ban <user_id> [reason]`\n\n"
            "**Example:**\n"
            "`/ban 123456789` - Ban user with ID 123456789\n"
            "`/ban 123456789 Spamming` - Ban with reason"
        )
        return
    
    try:
        target_user_id = int(message.command[1])
        ban_reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
        
        # Check if user exists
        user_exists = await codeflixbots.is_user_exist(target_user_id)
        
        if not user_exists:
            await message.reply_text(f"❌ User ID `{target_user_id}` not found in database.")
            return
        
        # Check if already banned
        is_already_banned = await codeflixbots.is_user_banned(target_user_id)
        
        if is_already_banned:
            ban_info = await codeflixbots.get_ban_info(target_user_id)
            banned_date = ban_info.get('banned_on', 'Unknown')
            reason = ban_info.get('ban_reason', 'No reason')
            
            await message.reply_text(
                f"⚠️ User `{target_user_id}` is already banned.\n\n"
                f"**Banned on:** {banned_date}\n"
                f"**Reason:** {reason}"
            )
            return
        
        # Ban the user
        success = await codeflixbots.ban_user(target_user_id, ban_reason)
        
        if success:
            # Try to get user info for logging
            try:
                target_user = await client.get_users(target_user_id)
                user_info = f"{target_user.mention} (`{target_user_id}`)"
            except:
                user_info = f"`{target_user_id}`"
            
            # Send success message
            await message.reply_text(
                f"✅ **User banned successfully!**\n\n"
                f"**User:** {user_info}\n"
                f"**Reason:** {ban_reason}\n"
                f"**Date:** {datetime.date.today().strftime('%d %B %Y')}"
            )
            
            # Log to LOG_CHANNEL
            if Config.LOG_CHANNEL:
                await client.send_message(
                    Config.LOG_CHANNEL,
                    f"🚫 **User Banned**\n\n"
                    f"**Admin:** {message.from_user.mention}\n"
                    f"**User ID:** `{target_user_id}`\n"
                    f"**Reason:** {ban_reason}\n"
                    f"**Date:** {datetime.date.today().strftime('%d %B %Y')}"
                )
            
            # Notify the banned user
            try:
                await client.send_message(
                    target_user_id,
                    f"🚫 **You have been banned from using this bot.**\n\n"
                    f"**Reason:** {ban_reason}\n"
                    f"**Date:** {datetime.date.today().strftime('%d %B %Y')}\n\n"
                    f"Contact admin if you think this is a mistake."
                )
            except:
                pass  # User might have blocked the bot or deleted account
        else:
            await message.reply_text("❌ Failed to ban user. Please try again.")
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@Client.on_message(filters.private & filters.command("unban") & filters.user(Config.ADMIN))
async def unban_user_command(client: Client, message: Message):
    """Unban a user - Admin only"""
    if len(message.command) < 2:
        await message.reply_text(
            "**Usage:** `/unban <user_id>`\n\n"
            "**Example:** `/unban 123456789`"
        )
        return
    
    try:
        target_user_id = int(message.command[1])
        
        # Check if user exists
        user_exists = await codeflixbots.is_user_exist(target_user_id)
        
        if not user_exists:
            await message.reply_text(f"❌ User ID `{target_user_id}` not found in database.")
            return
        
        # Check if user is actually banned
        is_banned = await codeflixbots.is_user_banned(target_user_id)
        
        if not is_banned:
            await message.reply_text(f"ℹ️ User `{target_user_id}` is not banned.")
            return
        
        # Unban the user
        success = await codeflixbots.unban_user(target_user_id)
        
        if success:
            # Try to get user info
            try:
                target_user = await client.get_users(target_user_id)
                user_info = f"{target_user.mention} (`{target_user_id}`)"
            except:
                user_info = f"`{target_user_id}`"
            
            # Send success message
            await message.reply_text(
                f"✅ **User unbanned successfully!**\n\n"
                f"**User:** {user_info}\n"
                f"**Date:** {datetime.date.today().strftime('%d %B %Y')}"
            )
            
            # Log to LOG_CHANNEL
            if Config.LOG_CHANNEL:
                await client.send_message(
                    Config.LOG_CHANNEL,
                    f"✅ **User Unbanned**\n\n"
                    f"**Admin:** {message.from_user.mention}\n"
                    f"**User ID:** `{target_user_id}`\n"
                    f"**Date:** {datetime.date.today().strftime('%d %B %Y')}"
                )
            
            # Notify the unbanned user
            try:
                await client.send_message(
                    target_user_id,
                    f"✅ **Your ban has been lifted!**\n\n"
                    f"You can now use the bot again.\n"
                    f"**Date:** {datetime.date.today().strftime('%d %B %Y')}"
                )
            except:
                pass  # User might have blocked the bot
            
        else:
            await message.reply_text("❌ Failed to unban user. Please try again.")
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

@Client.on_message(filters.private & filters.command("banlist") & filters.user(Config.ADMIN))
async def banlist_command(client: Client, message: Message):
    """Show list of banned users - Admin only"""
    try:
        banned_users = await codeflixbots.get_banned_users()
        
        if not banned_users:
            await message.reply_text("📋 **Ban List**\n\nNo users are currently banned.")
            return
        
        total_banned = len(banned_users)
        
        # Create message with banned users list
        ban_list_text = f"📋 **Ban List**\n\n"
        ban_list_text += f"**Total Banned Users:** {total_banned}\n\n"
        
        for i, user in enumerate(banned_users, 1):
            user_id = user['_id']
            ban_info = user.get('ban_status', {})
            ban_reason = ban_info.get('ban_reason', 'No reason')
            banned_date = ban_info.get('banned_on', 'Unknown')
            
            # Try to get username for better identification
            try:
                user_obj = await client.get_users(user_id)
                username = f"@{user_obj.username}" if user_obj.username else "No username"
                name = user_obj.first_name or "Unknown"
                user_display = f"{name} ({username})"
            except:
                user_display = f"ID: {user_id}"
            
            ban_list_text += f"**{i}. {user_display}**\n"
            ban_list_text += f"   ├ **ID:** `{user_id}`\n"
            ban_list_text += f"   ├ **Reason:** {ban_reason}\n"
            ban_list_text += f"   └ **Date:** {banned_date}\n\n"
        
        # Add summary
        ban_list_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        ban_list_text += f"Use `/unban <user_id>` to unban a user."
        
        # Split if message is too long
        if len(ban_list_text) > 4000:
            parts = [ban_list_text[i:i+4000] for i in range(0, len(ban_list_text), 4000)]
            for part in parts:
                await message.reply_text(part, disable_web_page_preview=True)
        else:
            await message.reply_text(ban_list_text, disable_web_page_preview=True)
            
    except Exception as e:
        await message.reply_text(f"❌ Error fetching ban list: {str(e)}")

# =====================================================
# BAN CHECK FOR ALL MESSAGES
# =====================================================

@Client.on_message(filters.private)
async def check_ban_on_message(client: Client, message: Message):
    """Check ban status for every message"""
    # Skip if message is from admin
    if message.from_user.id in Config.ADMIN:
        return
    
    # Check if user is banned
    is_banned = await check_ban_middleware(client, message)
    
    if is_banned:
        # Stop further processing for banned users
        raise StopPropagation

# =====================================================
# EXCEPTION FOR START COMMAND (FOR BANNED USERS)
# =====================================================

@Client.on_message(filters.private & filters.command("start"))
async def start_with_ban_check(client: Client, message: Message):
    """Start command with ban check"""
    user_id = message.from_user.id
    
    # Check if user is banned
    is_banned = await codeflixbots.is_user_banned(user_id)
    
    if is_banned:
        ban_info = await codeflixbots.get_ban_info(user_id)
        ban_reason = ban_info.get('ban_reason', 'No reason provided') if ban_info else 'No reason provided'
        banned_date = ban_info.get('banned_on', 'Unknown') if ban_info else 'Unknown'
        
        await message.reply_text(
            f"🚫 **You are banned from using this bot.**\n\n"
            f"**Reason:** {ban_reason}\n"
            f"**Date:** {banned_date}\n\n"
            f"You are not allowed to use this bot anymore."
        )
        return
    
    # If not banned, proceed with normal start
    # Call the existing start handler
    from plugins.start_&_cb import start
    await start(client, message)

from config import Config, Txt
from helper.database import n4bots
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import os, sys, time, asyncio, logging, datetime
from datetime import timedelta

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ADMIN_USER_ID = Config.ADMIN

# Flag to indicate if the bot is restarting
is_restarting = False

# =====================================================
# BAN CONTROL PANEL FUNCTIONS
# =====================================================

def format_ban_duration(seconds):
    """Format ban duration to human readable format"""
    if seconds == 0:
        return "Permanent"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "0m"

def get_ban_reason_emoji(reason):
    """Get emoji based on ban reason"""
    reason_lower = str(reason).lower()
    if any(word in reason_lower for word in ['spam', 'flood']):
        return "🚫"
    elif any(word in reason_lower for word in ['abuse', 'harassment']):
        return "⚠️"
    elif any(word in reason_lower for word in ['premium', 'payment']):
        return "💰"
    elif any(word in reason_lower for word in ['rules', 'terms']):
        return "📜"
    else:
        return "🔨"

async def get_ban_stats():
    """Get statistics about banned users"""
    try:
        # Count banned users
        banned_count = await n4bots.col.count_documents({
            "ban_status.is_banned": True
        })
        
        # Count permanent bans
        permanent_count = await n4bots.col.count_documents({
            "ban_status.is_banned": True,
            "ban_status.ban_duration": 0
        })
        
        # Count temporary bans
        temp_count = await n4bots.col.count_documents({
            "ban_status.is_banned": True,
            "ban_status.ban_duration": {"$gt": 0}
        })
        
        # Get recent bans (last 7 days)
        week_ago = (datetime.datetime.now() - timedelta(days=7)).isoformat()
        recent_count = await n4bots.col.count_documents({
            "ban_status.is_banned": True,
            "ban_status.banned_on": {"$gte": week_ago}
        })
        
        return {
            "total_banned": banned_count,
            "permanent": permanent_count,
            "temporary": temp_count,
            "recent_week": recent_count
        }
    except Exception as e:
        logger.error(f"Error getting ban stats: {e}")
        return None

async def ban_user(user_id, duration_days=0, reason="No reason provided"):
    """Ban a user"""
    try:
        ban_duration = duration_days * 86400 if duration_days > 0 else 0
        banned_on = datetime.datetime.now().isoformat()
        
        await n4bots.col.update_one(
            {"_id": int(user_id)},
            {"$set": {
                "ban_status.is_banned": True,
                "ban_status.ban_duration": ban_duration,
                "ban_status.banned_on": banned_on,
                "ban_status.ban_reason": reason
            }},
            upsert=True
        )
        
        # Delete user's verification status when banned
        await n4bots.delete_verify_status(user_id)
        
        return True, "User banned successfully"
    except Exception as e:
        logger.error(f"Error banning user {user_id}: {e}")
        return False, f"Error banning user: {str(e)}"

async def unban_user(user_id):
    """Unban a user"""
    try:
        await n4bots.col.update_one(
            {"_id": int(user_id)},
            {"$set": {
                "ban_status.is_banned": False,
                "ban_status.ban_duration": 0,
                "ban_status.banned_on": datetime.date.max.isoformat(),
                "ban_status.ban_reason": ""
            }}
        )
        return True, "User unbanned successfully"
    except Exception as e:
        logger.error(f"Error unbanning user {user_id}: {e}")
        return False, f"Error unbanning user: {str(e)}"

async def is_user_banned(user_id):
    """Check if a user is banned"""
    try:
        user = await n4bots.col.find_one({"_id": int(user_id)})
        if user and "ban_status" in user:
            return user["ban_status"].get("is_banned", False)
        return False
    except Exception as e:
        logger.error(f"Error checking ban status for user {user_id}: {e}")
        return False

async def get_banned_users(limit=50, offset=0):
    """Get list of banned users with pagination"""
    try:
        pipeline = [
            {"$match": {"ban_status.is_banned": True}},
            {"$sort": {"ban_status.banned_on": -1}},
            {"$skip": offset},
            {"$limit": limit},
            {"$project": {
                "_id": 1,
                "ban_status": 1,
                "join_date": 1
            }}
        ]
        
        banned_users = []
        async for user in n4bots.col.aggregate(pipeline):
            banned_users.append(user)
        
        return banned_users
    except Exception as e:
        logger.error(f"Error getting banned users: {e}")
        return []

async def search_banned_users(query):
    """Search banned users by ID or partial username"""
    try:
        # Try to convert query to integer for ID search
        try:
            user_id = int(query)
            user = await n4bots.col.find_one({
                "_id": user_id,
                "ban_status.is_banned": True
            })
            return [user] if user else []
        except ValueError:
            # If not a valid integer, search by partial match in username
            pass
        
        # Search for users with the query in their data
        users = []
        async for user in n4bots.col.find({
            "ban_status.is_banned": True,
            "$or": [
                {"_id": {"$regex": str(query), "$options": "i"}}
            ]
        }).limit(20):
            users.append(user)
        
        return users
    except Exception as e:
        logger.error(f"Error searching banned users: {e}")
        return []

# =====================================================
# BAN CONTROL PANEL COMMANDS
# =====================================================

@Client.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID))
async def ban_control_panel(client: Client, message: Message):
    """Main ban control panel"""
    # Get ban statistics
    stats = await get_ban_stats()
    
    if not stats:
        await message.reply_text("❌ Error retrieving ban statistics.")
        return
    
    text = f"""
🔨 **Ban Control Panel**

📊 **Statistics:**
├ Total Banned Users: `{stats['total_banned']}`
├ Permanent Bans: `{stats['permanent']}`
├ Temporary Bans: `{stats['temp_count']}`
└ Recent (7 days): `{stats['recent_week']}`

⚡ **Quick Actions:**
• Ban a user by ID
• View banned users list
• Search banned users
• Remove ban from users

📝 **Usage:**
`/ban add <user_id> <days> <reason>` - Ban user
`/ban list` - Show banned users
`/ban search <query>` - Search banned users
`/ban remove <user_id>` - Remove ban
`/ban stats` - View statistics
"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📋 Banned Users List", callback_data="ban_list_1"),
            InlineKeyboardButton("🔍 Search Users", callback_data="ban_search")
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="ban_stats"),
            InlineKeyboardButton("❌ Close", callback_data="close_ban_panel")
        ]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

@Client.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID) & filters.regex(r"^/ban add"))
async def ban_user_command(client: Client, message: Message):
    """Ban a user via command"""
    try:
        # Parse command: /ban add <user_id> <days> <reason>
        parts = message.text.split(maxsplit=4)
        
        if len(parts) < 5:
            await message.reply_text(
                "❌ **Incorrect format!**\n\n"
                "📝 **Correct format:**\n"
                "`/ban add <user_id> <days> <reason>`\n\n"
                "📌 **Example:**\n"
                "`/ban add 123456789 7 Spamming messages`\n\n"
                "💡 **Note:** Use `0` days for permanent ban."
            )
            return
        
        user_id = int(parts[2])
        days = int(parts[3])
        reason = parts[4]
        
        # Check if user exists
        if not await n4bots.is_user_exist(user_id):
            await message.reply_text(f"❌ User `{user_id}` not found in database.")
            return
        
        # Check if already banned
        if await is_user_banned(user_id):
            await message.reply_text(f"⚠️ User `{user_id}` is already banned.")
            return
        
        # Ban the user
        success, result_msg = await ban_user(user_id, days, reason)
        
        if success:
            duration_text = "permanent" if days == 0 else f"{days} day(s)"
            ban_message = (
                f"✅ **User Banned Successfully!**\n\n"
                f"👤 **User ID:** `{user_id}`\n"
                f"⏰ **Duration:** {duration_text}\n"
                f"📝 **Reason:** {reason}\n\n"
                f"⚠️ User can no longer use the bot."
            )
            
            # Try to notify the user
            try:
                await client.send_message(
                    user_id,
                    f"🚫 **You have been banned from using this bot.**\n\n"
                    f"**Reason:** {reason}\n"
                    f"**Duration:** {duration_text}\n\n"
                    f"Contact admin for more information."
                )
            except:
                pass  # User might have blocked the bot
            
            await message.reply_text(ban_message)
            
            # Log to admin channel
            try:
                await client.send_message(
                    Config.LOG_CHANNEL,
                    f"🔨 **User Banned**\n\n"
                    f"**By:** {message.from_user.mention}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Duration:** {duration_text}\n"
                    f"**Reason:** {reason}"
                )
            except:
                pass
        else:
            await message.reply_text(f"❌ {result_msg}")
            
    except ValueError:
        await message.reply_text("❌ **Invalid input!** Please provide valid numbers for user ID and days.")
    except Exception as e:
        logger.error(f"Error in ban command: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")

@Client.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID) & filters.regex(r"^/ban remove"))
async def unban_user_command(client: Client, message: Message):
    """Remove ban from a user"""
    try:
        parts = message.text.split(maxsplit=2)
        
        if len(parts) < 3:
            await message.reply_text(
                "❌ **Incorrect format!**\n\n"
                "📝 **Correct format:**\n"
                "`/ban remove <user_id>`\n\n"
                "📌 **Example:**\n"
                "`/ban remove 123456789`"
            )
            return
        
        user_id = int(parts[2])
        
        # Check if user exists
        if not await n4bots.is_user_exist(user_id):
            await message.reply_text(f"❌ User `{user_id}` not found in database.")
            return
        
        # Check if actually banned
        if not await is_user_banned(user_id):
            await message.reply_text(f"ℹ️ User `{user_id}` is not currently banned.")
            return
        
        # Unban the user
        success, result_msg = await unban_user(user_id)
        
        if success:
            unban_message = (
                f"✅ **User Unbanned Successfully!**\n\n"
                f"👤 **User ID:** `{user_id}`\n"
                f"🔄 **Status:** Can now use the bot again\n\n"
                f"💡 User verification status has been reset."
            )
            
            # Try to notify the user
            try:
                await client.send_message(
                    user_id,
                    "✅ **Your ban has been lifted!**\n\n"
                    "You can now use the bot again.\n"
                    "You may need to re-verify if required."
                )
            except:
                pass
            
            await message.reply_text(unban_message)
            
            # Log to admin channel
            try:
                await client.send_message(
                    Config.LOG_CHANNEL,
                    f"🔄 **User Unbanned**\n\n"
                    f"**By:** {message.from_user.mention}\n"
                    f"**User ID:** `{user_id}`"
                )
            except:
                pass
        else:
            await message.reply_text(f"❌ {result_msg}")
            
    except ValueError:
        await message.reply_text("❌ **Invalid input!** Please provide a valid user ID.")
    except Exception as e:
        logger.error(f"Error in unban command: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")

@Client.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID) & filters.regex(r"^/ban list"))
async def list_banned_users_command(client: Client, message: Message):
    """List banned users with pagination"""
    try:
        # Get page number from command
        parts = message.text.split()
        page = int(parts[2]) if len(parts) > 2 else 1
        
        if page < 1:
            page = 1
        
        limit = 10
        offset = (page - 1) * limit
        
        banned_users = await get_banned_users(limit, offset)
        total_count = (await get_ban_stats())["total_banned"]
        total_pages = (total_count + limit - 1) // limit
        
        if not banned_users:
            text = "📭 **No banned users found.**"
            if page > 1:
                text += f"\n\nPage {page} is empty. Try a lower page number."
            await message.reply_text(text)
            return
        
        text = f"🔨 **Banned Users List**\n\n"
        text += f"📊 **Page {page}/{total_pages}** | **Total: {total_count}**\n\n"
        
        for i, user in enumerate(banned_users, start=offset + 1):
            ban_info = user.get("ban_status", {})
            user_id = user.get("_id", "Unknown")
            banned_on = ban_info.get("banned_on", "Unknown")
            ban_duration = ban_info.get("ban_duration", 0)
            ban_reason = ban_info.get("ban_reason", "No reason")
            
            # Format date
            try:
                banned_date = datetime.datetime.fromisoformat(banned_on).strftime("%d %b %Y")
            except:
                banned_date = banned_on
            
            duration_text = format_ban_duration(ban_duration)
            emoji = get_ban_reason_emoji(ban_reason)
            
            text += f"{i}. `{user_id}`\n"
            text += f"   {emoji} **Reason:** {ban_reason}\n"
            text += f"   ⏰ **Duration:** {duration_text}\n"
            text += f"   📅 **Banned on:** {banned_date}\n\n"
        
        # Create pagination buttons
        buttons = []
        row = []
        
        if page > 1:
            row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"ban_list_{page-1}"))
        
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        
        if page < total_pages:
            row.append(InlineKeyboardButton("Next ➡️", callback_data=f"ban_list_{page+1}"))
        
        if row:
            buttons.append(row)
        
        buttons.extend([
            [InlineKeyboardButton("🔍 Search User", callback_data="ban_search")],
            [InlineKeyboardButton("📊 Statistics", callback_data="ban_stats")],
            [InlineKeyboardButton("❌ Close", callback_data="close_ban_panel")]
        ])
        
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as e:
        logger.error(f"Error listing banned users: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")

@Client.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID) & filters.regex(r"^/ban search"))
async def search_banned_users_command(client: Client, message: Message):
    """Search for banned users"""
    try:
        parts = message.text.split(maxsplit=2)
        
        if len(parts) < 3:
            await message.reply_text(
                "❌ **Incorrect format!**\n\n"
                "📝 **Correct format:**\n"
                "`/ban search <user_id>`\n\n"
                "📌 **Example:**\n"
                "`/ban search 123456789`"
            )
            return
        
        query = parts[2]
        users = await search_banned_users(query)
        
        if not users:
            await message.reply_text(f"🔍 No banned users found for query: `{query}`")
            return
        
        text = f"🔍 **Search Results for: `{query}`**\n\n"
        
        for i, user in enumerate(users, 1):
            ban_info = user.get("ban_status", {})
            user_id = user.get("_id", "Unknown")
            ban_reason = ban_info.get("ban_reason", "No reason")
            ban_duration = ban_info.get("ban_duration", 0)
            
            duration_text = format_ban_duration(ban_duration)
            emoji = get_ban_reason_emoji(ban_reason)
            
            text += f"{i}. `{user_id}`\n"
            text += f"   {emoji} **Reason:** {ban_reason}\n"
            text += f"   ⏰ **Duration:** {duration_text}\n"
            text += f"   🛠️ **Action:** /ban remove {user_id}\n\n"
        
        # Add action buttons
        buttons = [
            [InlineKeyboardButton("📋 All Banned Users", callback_data="ban_list_1")],
            [InlineKeyboardButton("📊 Statistics", callback_data="ban_stats")],
            [InlineKeyboardButton("❌ Close", callback_data="close_ban_panel")]
        ]
        
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        
    except Exception as e:
        logger.error(f"Error searching banned users: {e}")
        await message.reply_text(f"❌ Error: {str(e)}")

@Client.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID) & filters.regex(r"^/ban stats"))
async def ban_stats_command(client: Client, message: Message):
    """Show detailed ban statistics"""
    stats = await get_ban_stats()
    
    if not stats:
        await message.reply_text("❌ Error retrieving ban statistics.")
        return
    
    text = f"""
📊 **Ban Statistics**

📈 **Overview:**
├ Total Banned Users: `{stats['total_banned']}`
├ Permanent Bans: `{stats['permanent']}`
├ Temporary Bans: `{stats['temp_count']}`
└ Recent (7 days): `{stats['recent_week']}`

📋 **Quick Actions:**
• `/ban list` - View all banned users
• `/ban search <id>` - Search for a user
• `/ban add <id> <days> <reason>` - Ban a user
• `/ban remove <id>` - Unban a user

💡 **Tips:**
• Use `0` days for permanent bans
• Always provide a clear reason for bans
• Check recent bans weekly for review
"""
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Banned Users", callback_data="ban_list_1")],
        [InlineKeyboardButton("🔍 Search Users", callback_data="ban_search")],
        [InlineKeyboardButton("❌ Close", callback_data="close_ban_panel")]
    ])
    
    await message.reply_text(text, reply_markup=buttons)

# =====================================================
# BAN CONTROL PANEL CALLBACK HANDLERS
# =====================================================

@Client.on_callback_query(filters.regex(r"^ban_list_(\d+)$") & filters.user(ADMIN_USER_ID))
async def ban_list_callback(client: Client, query: CallbackQuery):
    """Handle ban list pagination"""
    try:
        page = int(query.data.split("_")[2])
        limit = 10
        offset = (page - 1) * limit
        
        banned_users = await get_banned_users(limit, offset)
        total_count = (await get_ban_stats())["total_banned"]
        total_pages = (total_count + limit - 1) // limit
        
        if not banned_users:
            await query.answer("No more banned users.", show_alert=True)
            return
        
        text = f"🔨 **Banned Users List**\n\n"
        text += f"📊 **Page {page}/{total_pages}** | **Total: {total_count}**\n\n"
        
        for i, user in enumerate(banned_users, start=offset + 1):
            ban_info = user.get("ban_status", {})
            user_id = user.get("_id", "Unknown")
            banned_on = ban_info.get("banned_on", "Unknown")
            ban_duration = ban_info.get("ban_duration", 0)
            ban_reason = ban_info.get("ban_reason", "No reason")
            
            try:
                banned_date = datetime.datetime.fromisoformat(banned_on).strftime("%d %b %Y")
            except:
                banned_date = banned_on
            
            duration_text = format_ban_duration(ban_duration)
            emoji = get_ban_reason_emoji(ban_reason)
            
            text += f"{i}. `{user_id}`\n"
            text += f"   {emoji} **Reason:** {ban_reason}\n"
            text += f"   ⏰ **Duration:** {duration_text}\n"
            text += f"   📅 **Banned on:** {banned_date}\n\n"
        
        # Update buttons
        buttons = []
        row = []
        
        if page > 1:
            row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"ban_list_{page-1}"))
        
        row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))
        
        if page < total_pages:
            row.append(InlineKeyboardButton("Next ➡️", callback_data=f"ban_list_{page+1}"))
        
        if row:
            buttons.append(row)
        
        buttons.extend([
            [InlineKeyboardButton("🔍 Search User", callback_data="ban_search")],
            [InlineKeyboardButton("📊 Statistics", callback_data="ban_stats")],
            [InlineKeyboardButton("❌ Close", callback_data="close_ban_panel")]
        ])
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        await query.answer()
        
    except Exception as e:
        logger.error(f"Error in ban list callback: {e}")
        await query.answer("Error loading page.", show_alert=True)

@Client.on_callback_query(filters.regex("^ban_search$") & filters.user(ADMIN_USER_ID))
async def ban_search_callback(client: Client, query: CallbackQuery):
    """Handle ban search callback"""
    await query.message.edit_text(
        "🔍 **Search Banned Users**\n\n"
        "Send me the user ID to search for.\n"
        "Example: `123456789`\n\n"
        "Or type: `/ban search <user_id>`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 All Banned Users", callback_data="ban_list_1")],
            [InlineKeyboardButton("📊 Statistics", callback_data="ban_stats")],
            [InlineKeyboardButton("❌ Cancel", callback_data="close_ban_panel")]
        ])
    )
    await query.answer()

@Client.on_callback_query(filters.regex("^ban_stats$") & filters.user(ADMIN_USER_ID))
async def ban_stats_callback(client: Client, query: CallbackQuery):
    """Handle ban stats callback"""
    stats = await get_ban_stats()
    
    if not stats:
        await query.answer("Error retrieving statistics.", show_alert=True)
        return
    
    text = f"""
📊 **Ban Statistics**

📈 **Overview:**
├ Total Banned Users: `{stats['total_banned']}`
├ Permanent Bans: `{stats['permanent']}`
├ Temporary Bans: `{stats['temp_count']}`
└ Recent (7 days): `{stats['recent_week']}`

📋 **Quick Actions:**
• `/ban list` - View all banned users
• `/ban search <id>` - Search for a user
• `/ban add <id> <days> <reason>` - Ban a user
• `/ban remove <id>` - Unban a user
"""
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Banned Users", callback_data="ban_list_1")],
        [InlineKeyboardButton("🔍 Search Users", callback_data="ban_search")],
        [InlineKeyboardButton("❌ Close", callback_data="close_ban_panel")]
    ])
    
    await query.message.edit_text(text, reply_markup=buttons)
    await query.answer()

@Client.on_callback_query(filters.regex("^close_ban_panel$") & filters.user(ADMIN_USER_ID))
async def close_ban_panel_callback(client: Client, query: CallbackQuery):
    """Close ban control panel"""
    await query.message.delete()
    await query.answer("Panel closed")

@Client.on_callback_query(filters.regex("^noop$"))
async def noop_callback(client: Client, query: CallbackQuery):
    """Handle no-operation callback"""
    await query.answer()

# =====================================================
# EXISTING ADMIN FUNCTIONS (keep these unchanged)
# =====================================================

@Client.on_message(filters.private & filters.command("restart") & filters.user(ADMIN_USER_ID))
async def restart_bot(b, m):
    global is_restarting
    if not is_restarting:
        is_restarting = True
        await m.reply_text("**Restarting.....**")

        # Gracefully stop the bot's event loop
        b.stop()
        time.sleep(2)  # Adjust the delay duration based on your bot's shutdown time

        # Restart the bot process
        os.execl(sys.executable, sys.executable, *sys.argv)


@Client.on_message(filters.private & filters.command("tutorial"))
async def tutorial(bot: Client, message: Message):
    user_id = message.from_user.id
    format_template = await n4bots.get_format_template(user_id)
    await message.reply_text(
        text=Txt.FILE_NAME_TXT.format(format_template=format_template),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(" ᴏᴡɴᴇʀ", url="https://t.me/Anime_library_n4"),
             InlineKeyboardButton(" ᴛᴜᴛᴏʀɪᴀʟ", url="https://t.me/Animelibraryn4")]
        ])
    )


@Client.on_message(filters.command(["stats", "status"]) & filters.user(Config.ADMIN))
async def get_stats(bot, message):
    total_users = await n4bots.total_users_count()
    # Simple uptime - calculate from when bot started
    if hasattr(bot, 'start_time'):
        uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - bot.start_time))
    else:
        uptime = "Unknown"    
    start_t = time.time()
    st = await message.reply('**Accessing The Details.....**')    
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await st.edit(text=f"**--Bot Status--** \n\n**⌚️ Bot Uptime :** {uptime} \n**🐌 Current Ping :** `{time_taken_s:.3f} ms` \n**👭 Total Users :** `{total_users}`")

@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN) & filters.reply)
async def broadcast_handler(bot: Client, m: Message):
    """Fixed broadcast function - simpler and more reliable"""
    
    # Send to log channel
    try:
        await bot.send_message(
            Config.LOG_CHANNEL, 
            f"📢 {m.from_user.mention} ({m.from_user.id}) started a broadcast"
        )
    except:
        pass  # Don't stop if log channel fails
    
    # Get the message to broadcast
    broadcast_msg = m.reply_to_message
    
    # Get all users
    all_users = await n4bots.get_all_users()
    total_users = await n4bots.total_users_count()
    
    # Start message
    sts_msg = await m.reply_text(f"📢 **Starting Broadcast...**\nTotal Users: {total_users}\nStatus: Preparing...")
    
    success = 0
    failed = 0
    deleted = 0
    progress = 0
    
    # Track start time
    import datetime
    start_time = time.time()
    
    # Process users
    async for user in all_users:
        try:
            user_id = user['_id']
            
            # Try to send message
            try:
                await broadcast_msg.copy(chat_id=int(user_id))
                success += 1
                
            # Handle various errors
            except FloodWait as e:
                # Wait for flood control
                await asyncio.sleep(e.value)
                # Try again
                try:
                    await broadcast_msg.copy(chat_id=int(user_id))
                    success += 1
                except:
                    failed += 1
                    
            except (InputUserDeactivated, UserIsBlocked):
                # User blocked or deleted account
                deleted += 1
                await n4bots.delete_user(user_id)
                
            except PeerIdInvalid:
                # Invalid user ID
                failed += 1
                
            except Exception as e:
                # Any other error
                failed += 1
                
        except Exception as e:
            # Error processing user
            failed += 1
        
        # Update progress every 20 users or 5 seconds
        progress += 1
        if progress % 20 == 0 or time.time() - start_time > 5:
            try:
                await sts_msg.edit_text(
                    f"📢 **Broadcast in Progress**\n\n"
                    f"• ✅ Success: {success}\n"
                    f"• ❌ Failed: {failed}\n"
                    f"• 🗑️ Deleted: {deleted}\n"
                    f"• 📊 Progress: {progress}/{total_users}\n"
                    f"• ⏱️ Time: {int(time.time() - start_time)}s"
                )
            except:
                pass  # Don't crash if edit fails
    
    # Calculate time taken
    completed_in = int(time.time() - start_time)
    
    # Final message
    await sts_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"📊 **Statistics:**\n"
        f"• ✅ Successfully sent: {success}\n"
        f"• ❌ Failed to send: {failed}\n"
        f"• 🗑️ Inactive users removed: {deleted}\n"
        f"• ⏱️ Time taken: {completed_in} seconds\n"
        f"• 📈 Success rate: {round((success/total_users)*100, 2) if total_users > 0 else 0}%"
    )

async def send_msg(user_id, message):
    """Simple function to send message to a user"""
    try:
        await message.copy(chat_id=int(user_id))
        return 200  # Success
    except FloodWait as e:
        # Wait and try again
        await asyncio.sleep(e.value)
        try:
            await message.copy(chat_id=int(user_id))
            return 200
        except:
            return 400  # Failed after retry
    except (InputUserDeactivated, UserIsBlocked):
        return 400  # User blocked or deleted
    except PeerIdInvalid:
        return 400  # Invalid user ID
    except Exception as e:
        print(f"Broadcast error for user {user_id}: {e}")
        return 500  # Other error

from config import Config, Txt
from helper.database import n4bots
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import os, sys, time, asyncio, logging, datetime
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ADMIN_USER_ID = Config.ADMIN

# Flag to indicate if the bot is restarting
is_restarting = False

# =============================
# BAN CONTROL PANEL
# =============================

@Client.on_message(filters.private & filters.command("ban") & filters.user(ADMIN_USER_ID))
async def ban_control_panel(bot: Client, message: Message):
    """Ban Control Panel - Main Menu"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban User", callback_data="ban_user")],
        [InlineKeyboardButton("📋 View Banned Users", callback_data="view_banned")],
        [InlineKeyboardButton("✅ Unban User", callback_data="unban_user")],
        [InlineKeyboardButton("❌ Close", callback_data="close_ban_panel")]
    ])
    
    await message.reply_text(
        "**🔨 Ban Control Panel**\n\n"
        "Select an option to manage user bans:",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^ban_user$") & filters.user(ADMIN_USER_ID))
async def ban_user_handler(client: Client, callback_query):
    """Initiate user banning process"""
    await callback_query.message.edit_text(
        "**🚫 Ban User**\n\n"
        "Please reply to a user's message with `/ban <reason>` or send:\n"
        "`/ban <user_id> <reason>`\n\n"
        "**Example:**\n"
        "`/ban 1234567890 Spamming`\n\n"
        "Or reply to any user's message with `/ban Violating rules`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
        ])
    )
    await callback_query.answer()

@Client.on_callback_query(filters.regex("^view_banned$") & filters.user(ADMIN_USER_ID))
async def view_banned_users(client: Client, callback_query):
    """Display list of banned users"""
    try:
        # Find all banned users
        banned_users = []
        async for user in n4bots.col.find({"ban_status.is_banned": True}):
            banned_users.append(user)
        
        if not banned_users:
            await callback_query.message.edit_text(
                "**📋 Banned Users List**\n\n"
                "No users are currently banned.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
                ])
            )
            return
        
        # Create paginated view
        items_per_page = 5
        total_pages = (len(banned_users) + items_per_page - 1) // items_per_page
        
        # Get current page from callback data if available
        page = 1
        if callback_query.data.startswith("view_banned_"):
            try:
                page = int(callback_query.data.split("_")[2])
            except:
                page = 1
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(banned_users))
        
        text = f"**📋 Banned Users List**\n\n"
        text += f"**Total Banned:** {len(banned_users)}\n"
        text += f"**Page:** {page}/{total_pages}\n\n"
        
        for i in range(start_idx, end_idx):
            user = banned_users[i]
            user_id = user.get("_id", "Unknown")
            ban_reason = user.get("ban_status", {}).get("ban_reason", "No reason provided")
            banned_on = user.get("ban_status", {}).get("banned_on", "Unknown date")
            ban_duration = user.get("ban_status", {}).get("ban_duration", 0)
            
            # Format duration
            if ban_duration == 0:
                duration_text = "Permanent"
            else:
                duration_text = f"{ban_duration} days"
            
            text += f"**{i+1}. User ID:** `{user_id}`\n"
            text += f"   **Reason:** {ban_reason}\n"
            text += f"   **Duration:** {duration_text}\n"
            text += f"   **Banned on:** {banned_on}\n\n"
        
        # Create navigation buttons
        buttons = []
        if total_pages > 1:
            row = []
            if page > 1:
                row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"view_banned_{page-1}"))
            row.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="none"))
            if page < total_pages:
                row.append(InlineKeyboardButton("Next ➡️", callback_data=f"view_banned_{page+1}"))
            buttons.append(row)
        
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")])
        
        await callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        logger.error(f"Error viewing banned users: {e}")
        await callback_query.message.edit_text(
            f"**Error:** {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
            ])
        )
    
    await callback_query.answer()

@Client.on_callback_query(filters.regex("^unban_user$") & filters.user(ADMIN_USER_ID))
async def unban_user_handler(client: Client, callback_query):
    """Initiate user unbanning process"""
    await callback_query.message.edit_text(
        "**✅ Unban User**\n\n"
        "Please reply to a banned user's message with `/unban` or send:\n"
        "`/unban <user_id>`\n\n"
        "**Example:**\n"
        "`/unban 1234567890`\n\n"
        "Or reply to any user's message with `/unban`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
        ])
    )
    await callback_query.answer()

@Client.on_callback_query(filters.regex("^close_ban_panel$"))
async def close_ban_panel(client: Client, callback_query):
    """Close the ban control panel"""
    await callback_query.message.delete()
    await callback_query.answer("Ban panel closed")

@Client.on_callback_query(filters.regex("^back_to_ban_panel$") & filters.user(ADMIN_USER_ID))
async def back_to_ban_panel(client: Client, callback_query):
    """Return to main ban panel"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚫 Ban User", callback_data="ban_user")],
        [InlineKeyboardButton("📋 View Banned Users", callback_data="view_banned")],
        [InlineKeyboardButton("✅ Unban User", callback_data="unban_user")],
        [InlineKeyboardButton("❌ Close", callback_data="close_ban_panel")]
    ])
    
    await callback_query.message.edit_text(
        "**🔨 Ban Control Panel**\n\n"
        "Select an option to manage user bans:",
        reply_markup=keyboard
    )
    await callback_query.answer()

@Client.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID) & filters.private)
async def ban_user_command(bot: Client, message: Message):
    """Ban a user by ID or reply"""
    try:
        # Check if replying to a message
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason provided"
        else:
            # Parse from command arguments
            if len(message.command) < 2:
                await message.reply_text(
                    "**Usage:**\n"
                    "`/ban <user_id> <reason>`\n"
                    "or reply to a message with `/ban <reason>`"
                )
                return
            
            try:
                user_id = int(message.command[1])
                reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
            except ValueError:
                await message.reply_text("Invalid user ID. Please provide a numeric user ID.")
                return
        
        # Check if user exists
        if not await n4bots.is_user_exist(user_id):
            await message.reply_text(f"User ID `{user_id}` not found in database.")
            return
        
        # Check if already banned
        user_data = await n4bots.col.find_one({"_id": user_id})
        if user_data and user_data.get("ban_status", {}).get("is_banned", False):
            await message.reply_text(f"User `{user_id}` is already banned.")
            return
        
        # Set ban status
        ban_duration = 0  # 0 means permanent ban
        banned_on = datetime.date.today().isoformat()
        
        await n4bots.col.update_one(
            {"_id": user_id},
            {"$set": {
                "ban_status": {
                    "is_banned": True,
                    "ban_duration": ban_duration,
                    "banned_on": banned_on,
                    "ban_reason": reason
                }
            }}
        )
        
        # Try to notify the user
        try:
            await bot.send_message(
                user_id,
                f"🚫 **You have been banned from using this bot.**\n\n"
                f"**Reason:** {reason}\n"
                f"**Duration:** Permanent\n"
                f"**Date:** {banned_on}\n\n"
                f"Contact @Animelibraryn4 if you believe this is a mistake."
            )
        except:
            pass  # User might have blocked the bot
        
        # Log to admin
        await message.reply_text(
            f"✅ **User banned successfully!**\n\n"
            f"**User ID:** `{user_id}`\n"
            f"**Reason:** {reason}\n"
            f"**Duration:** Permanent\n"
            f"**Date:** {banned_on}"
        )
        
        # Log to log channel if configured
        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"🚫 **User Banned**\n\n"
                    f"**By:** {message.from_user.mention} ({message.from_user.id})\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Reason:** {reason}\n"
                    f"**Date:** {banned_on}"
                )
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await message.reply_text(f"Error banning user: {str(e)}")

@Client.on_message(filters.command("tempban") & filters.user(ADMIN_USER_ID) & filters.private)
async def temp_ban_user_command(bot: Client, message: Message):
    """Temporarily ban a user"""
    try:
        # Check if replying to a message
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            if len(message.command) < 2:
                await message.reply_text(
                    "**Usage:**\n"
                    "`/tempban <days> <reason>`\n"
                    "or reply to a message with `/tempban <days> <reason>`"
                )
                return
            
            try:
                days = int(message.command[1])
                reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason provided"
            except ValueError:
                await message.reply_text("Invalid number of days. Please provide a valid number.")
                return
        else:
            # Parse from command arguments
            if len(message.command) < 3:
                await message.reply_text(
                    "**Usage:**\n"
                    "`/tempban <user_id> <days> <reason>`\n"
                    "or reply to a message with `/tempban <days> <reason>`"
                )
                return
            
            try:
                user_id = int(message.command[1])
                days = int(message.command[2])
                reason = " ".join(message.command[3:]) if len(message.command) > 3 else "No reason provided"
            except ValueError:
                await message.reply_text("Invalid user ID or days. Please provide numeric values.")
                return
        
        # Check if user exists
        if not await n4bots.is_user_exist(user_id):
            await message.reply_text(f"User ID `{user_id}` not found in database.")
            return
        
        # Check if already banned
        user_data = await n4bots.col.find_one({"_id": user_id})
        if user_data and user_data.get("ban_status", {}).get("is_banned", False):
            await message.reply_text(f"User `{user_id}` is already banned.")
            return
        
        # Set ban status
        banned_on = datetime.date.today().isoformat()
        
        await n4bots.col.update_one(
            {"_id": user_id},
            {"$set": {
                "ban_status": {
                    "is_banned": True,
                    "ban_duration": days,
                    "banned_on": banned_on,
                    "ban_reason": reason
                }
            }}
        )
        
        # Calculate unban date
        unban_date = datetime.date.today() + datetime.timedelta(days=days)
        
        # Try to notify the user
        try:
            await bot.send_message(
                user_id,
                f"🚫 **You have been temporarily banned from using this bot.**\n\n"
                f"**Reason:** {reason}\n"
                f"**Duration:** {days} day(s)\n"
                f"**Banned on:** {banned_on}\n"
                f"**Will be unbanned on:** {unban_date.isoformat()}\n\n"
                f"Contact @Animelibraryn4 if you believe this is a mistake."
            )
        except:
            pass  # User might have blocked the bot
        
        # Log to admin
        await message.reply_text(
            f"✅ **User temporarily banned successfully!**\n\n"
            f"**User ID:** `{user_id}`\n"
            f"**Reason:** {reason}\n"
            f"**Duration:** {days} day(s)\n"
            f"**Banned on:** {banned_on}\n"
            f"**Will be unbanned on:** {unban_date.isoformat()}"
        )
        
        # Log to log channel if configured
        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"🚫 **User Temporarily Banned**\n\n"
                    f"**By:** {message.from_user.mention} ({message.from_user.id})\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Reason:** {reason}\n"
                    f"**Duration:** {days} day(s)\n"
                    f"**Date:** {banned_on}\n"
                    f"**Unban on:** {unban_date.isoformat()}"
                )
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error temporarily banning user: {e}")
        await message.reply_text(f"Error banning user: {str(e)}")

@Client.on_message(filters.command("unban") & filters.user(ADMIN_USER_ID) & filters.private)
async def unban_user_command(bot: Client, message: Message):
    """Unban a user"""
    try:
        # Check if replying to a message
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            # Parse from command arguments
            if len(message.command) < 2:
                await message.reply_text(
                    "**Usage:**\n"
                    "`/unban <user_id>`\n"
                    "or reply to a message with `/unban`"
                )
                return
            
            try:
                user_id = int(message.command[1])
            except ValueError:
                await message.reply_text("Invalid user ID. Please provide a numeric user ID.")
                return
        
        # Check if user exists
        if not await n4bots.is_user_exist(user_id):
            await message.reply_text(f"User ID `{user_id}` not found in database.")
            return
        
        # Check if actually banned
        user_data = await n4bots.col.find_one({"_id": user_id})
        if not user_data or not user_data.get("ban_status", {}).get("is_banned", False):
            await message.reply_text(f"User `{user_id}` is not banned.")
            return
        
        # Remove ban status
        await n4bots.col.update_one(
            {"_id": user_id},
            {"$set": {
                "ban_status": {
                    "is_banned": False,
                    "ban_duration": 0,
                    "banned_on": datetime.date.max.isoformat(),
                    "ban_reason": ''
                }
            }}
        )
        
        # Try to notify the user
        try:
            await bot.send_message(
                user_id,
                "✅ **Your ban has been lifted!**\n\n"
                "You can now use the bot again.\n\n"
                "Thank you for your patience."
            )
        except:
            pass  # User might have blocked the bot
        
        # Log to admin
        await message.reply_text(
            f"✅ **User unbanned successfully!**\n\n"
            f"**User ID:** `{user_id}`\n"
            f"**Previous ban reason:** {user_data.get('ban_status', {}).get('ban_reason', 'No reason')}"
        )
        
        # Log to log channel if configured
        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"✅ **User Unbanned**\n\n"
                    f"**By:** {message.from_user.mention} ({message.from_user.id})\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Previous reason:** {user_data.get('ban_status', {}).get('ban_reason', 'No reason')}\n"
                    f"**Date:** {datetime.date.today().isoformat()}"
                )
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await message.reply_text(f"Error unbanning user: {str(e)}")

@Client.on_message(filters.command("baninfo") & filters.user(ADMIN_USER_ID) & filters.private)
async def ban_info_command(bot: Client, message: Message):
    """Get ban information for a user"""
    try:
        # Check if replying to a message
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            # Parse from command arguments
            if len(message.command) < 2:
                await message.reply_text(
                    "**Usage:**\n"
                    "`/baninfo <user_id>`\n"
                    "or reply to a message with `/baninfo`"
                )
                return
            
            try:
                user_id = int(message.command[1])
            except ValueError:
                await message.reply_text("Invalid user ID. Please provide a numeric user ID.")
                return
        
        # Get user data
        user_data = await n4bots.col.find_one({"_id": user_id})
        
        if not user_data:
            await message.reply_text(f"User ID `{user_id}` not found in database.")
            return
        
        ban_status = user_data.get("ban_status", {})
        is_banned = ban_status.get("is_banned", False)
        
        if not is_banned:
            await message.reply_text(f"User `{user_id}` is not banned.")
            return
        
        # Format ban information
        ban_reason = ban_status.get("ban_reason", "No reason provided")
        banned_on = ban_status.get("banned_on", "Unknown date")
        ban_duration = ban_status.get("ban_duration", 0)
        
        if ban_duration == 0:
            duration_text = "Permanent"
            unban_text = "Never (permanent ban)"
        else:
            duration_text = f"{ban_duration} day(s)"
            # Calculate unban date
            try:
                banned_date = datetime.date.fromisoformat(banned_on)
                unban_date = banned_date + datetime.timedelta(days=ban_duration)
                today = datetime.date.today()
                
                if unban_date < today:
                    unban_text = f"Already expired (was {unban_date.isoformat()})"
                else:
                    days_left = (unban_date - today).days
                    unban_text = f"{unban_date.isoformat()} ({days_left} day(s) left)"
            except:
                unban_text = "Unknown"
        
        text = f"**🔍 Ban Information for User `{user_id}`**\n\n"
        text += f"**Status:** 🚫 Banned\n"
        text += f"**Reason:** {ban_reason}\n"
        text += f"**Duration:** {duration_text}\n"
        text += f"**Banned on:** {banned_on}\n"
        text += f"**Will be unbanned:** {unban_text}\n\n"
        
        # Add user info if available
        try:
            user = await bot.get_users(user_id)
            text += f"**User:** {user.mention}\n"
            text += f"**Username:** @{user.username if user.username else 'N/A'}\n"
            text += f"**First Name:** {user.first_name or 'N/A'}\n"
            if user.last_name:
                text += f"**Last Name:** {user.last_name}\n"
        except:
            text += "**User details:** Could not fetch user info\n"
        
        await message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Error getting ban info: {e}")
        await message.reply_text(f"Error getting ban information: {str(e)}")

# =============================
# EXISTING FUNCTIONS (KEPT AS IS)
# =============================

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

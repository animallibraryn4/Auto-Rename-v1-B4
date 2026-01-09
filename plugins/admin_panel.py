from config import Config, Txt
from helper.database import n4bots
from pyrogram.types import Message
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from pyrogram import StopPropagation
import os, sys, time, asyncio, logging, datetime
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ADMIN_USER_ID = Config.ADMIN

# Flag to indicate if the bot is restarting
is_restarting = False

# State management for ban panel
ban_waiting_for_user_id = {}

# =============================
# EXISTING ADMIN COMMANDS (MODIFIED)
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
    """Handle /tutorial command with ban check"""
    # Check if user is banned (skip for admin)
    if message.from_user.id != ADMIN_USER_ID:
        is_banned = await check_ban_status(bot, message)
        if is_banned:
            return
    
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
            
            # Check if user is banned before sending
            user_data = await n4bots.col.find_one({"_id": int(user_id)})
            if user_data and user_data.get("ban_status", {}).get("is_banned", False):
                failed += 1
                progress += 1
                continue
            
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

# =============================
# NEW BAN CONTROL PANEL
# =============================

@Client.on_message(filters.private & filters.command("ban") & filters.user(ADMIN_USER_ID))
async def ban_control_panel(bot: Client, message: Message):
    """Ban Control Panel - Main Menu"""
    # Clean up any waiting state
    user_id = message.from_user.id
    if user_id in ban_waiting_for_user_id:
        del ban_waiting_for_user_id[user_id]
    
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
    """Initiate user banning process - ask for user ID only"""
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.id
    
    # Store state
    ban_waiting_for_user_id[user_id] = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    
    await callback_query.message.edit_text(
        "**🚫 Ban User**\n\n"
        "Please send the User ID you want to ban.\n\n"
        "Only send the numeric user ID.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
        ])
    )
    await callback_query.answer()

@Client.on_message(filters.private & filters.user(ADMIN_USER_ID) & filters.text)
async def process_admin_text_messages(bot: Client, message: Message):
    """Process admin text messages for ban/unban operations"""
    user_id = message.from_user.id
    
    # Check if we're waiting for user ID input for banning
    if user_id in ban_waiting_for_user_id:
        action = ban_waiting_for_user_id[user_id].get("action", "ban")
        
        if action == "ban":
            await process_ban_user_id(bot, message)
        elif action == "unban":
            await process_unban_user_id(bot, message)

async def process_ban_user_id(bot: Client, message: Message):
    """Process user ID input for banning"""
    user_id = message.from_user.id
    
    try:
        target_user_id = int(message.text.strip())
        
        # Remove the state
        state_data = ban_waiting_for_user_id.pop(user_id)
        chat_id = state_data["chat_id"]
        message_id = state_data["message_id"]
        
        # Check if user exists
        if not await n4bots.is_user_exist(target_user_id):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"❌ User ID `{target_user_id}` not found in database.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
                ])
            )
            return
        
        # Check if already banned
        user_data = await n4bots.col.find_one({"_id": target_user_id})
        if user_data and user_data.get("ban_status", {}).get("is_banned", False):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"❌ User `{target_user_id}` is already banned.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
                ])
            )
            return
        
        # Ban the user
        reason = "Banned by admin"
        banned_on = datetime.date.today().isoformat()
        
        await n4bots.col.update_one(
            {"_id": target_user_id},
            {"$set": {
                "ban_status": {
                    "is_banned": True,
                    "ban_duration": 0,
                    "banned_on": banned_on,
                    "ban_reason": reason
                }
            }}
        )
        
        # Update the original message with success
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ **Successfully banned the user**\n\nUser ID: `{target_user_id}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
            ])
        )
        
        # Delete the user's ID input message
        try:
            await message.delete()
        except:
            pass
        
        # Try to notify the banned user
        try:
            await bot.send_message(
                target_user_id,
                f"🚫 **You have been banned from using this bot.**\n\n"
                f"**Reason:** {reason}\n"
                f"**Duration:** Permanent\n"
                f"**Date:** {banned_on}\n\n"
                f"Contact @Animelibraryn4 if you believe this is a mistake."
            )
        except:
            pass
        
        # Log to log channel if configured
        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"🚫 **User Banned**\n\n"
                    f"**By:** {message.from_user.mention} ({message.from_user.id})\n"
                    f"**User ID:** `{target_user_id}`\n"
                    f"**Reason:** {reason}\n"
                    f"**Date:** {banned_on}"
                )
            except:
                pass
                
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please send only numeric user ID.")
    except Exception as e:
        logger.error(f"Error processing ban user ID: {e}")
        await message.reply_text(f"Error: {str(e)}")

@Client.on_callback_query(filters.regex("^view_banned$") & filters.user(ADMIN_USER_ID))
async def view_banned_users(client: Client, callback_query):
    """Display all banned users"""
    try:
        # Find all banned users
        banned_users = []
        async for user in n4bots.col.find({"ban_status.is_banned": True}):
            user_id = user.get("_id")
            ban_reason = user.get("ban_status", {}).get("ban_reason", "No reason")
            banned_on = user.get("ban_status", {}).get("banned_on", "Unknown")
            ban_duration = user.get("ban_status", {}).get("ban_duration", 0)
            
            banned_users.append({
                "user_id": user_id,
                "reason": ban_reason,
                "date": banned_on,
                "duration": ban_duration
            })
        
        if not banned_users:
            text = "📋 **Banned Users List**\n\nNo users are currently banned."
        else:
            text = f"📋 **Banned Users List**\n\nTotal Banned: {len(banned_users)}\n\n"
            for i, user in enumerate(banned_users[:50], 1):  # Limit to 50 users
                duration_text = "Permanent" if user['duration'] == 0 else f"{user['duration']} days"
                text += f"{i}. `{user['user_id']}`\n"
                text += f"   Reason: {user['reason']}\n"
                text += f"   Date: {user['date']}\n"
                text += f"   Duration: {duration_text}\n\n"
            
            if len(banned_users) > 50:
                text += f"\n... and {len(banned_users) - 50} more users."
        
        await callback_query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
            ])
        )
    except Exception as e:
        logger.error(f"Error viewing banned users: {e}")
        await callback_query.message.edit_text(
            f"❌ Error fetching banned users: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
            ])
        )
    await callback_query.answer()

@Client.on_callback_query(filters.regex("^unban_user$") & filters.user(ADMIN_USER_ID))
async def unban_user_handler(client: Client, callback_query):
    """Initiate user unbanning process"""
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.id
    
    # Store state for unban
    ban_waiting_for_user_id[user_id] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "action": "unban"
    }
    
    await callback_query.message.edit_text(
        "**✅ Unban User**\n\n"
        "Please send the User ID you want to unban.\n\n"
        "Only send the numeric user ID.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
        ])
    )
    await callback_query.answer()

async def process_unban_user_id(bot: Client, message: Message):
    """Process user ID input for unbanning"""
    user_id = message.from_user.id
    
    try:
        target_user_id = int(message.text.strip())
        
        # Remove the state
        state_data = ban_waiting_for_user_id.pop(user_id)
        chat_id = state_data["chat_id"]
        message_id = state_data["message_id"]
        
        # Check if user exists
        if not await n4bots.is_user_exist(target_user_id):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"❌ User ID `{target_user_id}` not found in database.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
                ])
            )
            return
        
        # Check if actually banned
        user_data = await n4bots.col.find_one({"_id": target_user_id})
        if not user_data or not user_data.get("ban_status", {}).get("is_banned", False):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"❌ User `{target_user_id}` is not banned.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
                ])
            )
            return
        
        # Unban the user
        await n4bots.col.update_one(
            {"_id": target_user_id},
            {"$set": {
                "ban_status": {
                    "is_banned": False,
                    "ban_duration": 0,
                    "banned_on": datetime.date.max.isoformat(),
                    "ban_reason": ''
                }
            }}
        )
        
        # Update the original message with success
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"✅ **Successfully unbanned the user**\n\nUser ID: `{target_user_id}`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_ban_panel")]
            ])
        )
        
        # Delete the user's ID input message
        try:
            await message.delete()
        except:
            pass
        
        # Try to notify the unbanned user
        try:
            await bot.send_message(
                target_user_id,
                f"✅ **Your ban has been lifted.**\n\n"
                f"You can now use the bot again.\n\n"
                f"If you have any questions, contact @Animelibraryn4."
            )
        except:
            pass
        
        # Log to log channel if configured
        if hasattr(Config, 'LOG_CHANNEL') and Config.LOG_CHANNEL:
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"✅ **User Unbanned**\n\n"
                    f"**By:** {message.from_user.mention} ({message.from_user.id})\n"
                    f"**User ID:** `{target_user_id}`\n"
                    f"**Date:** {datetime.date.today().isoformat()}"
                )
            except:
                pass
                
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please send only numeric user ID.")
    except Exception as e:
        logger.error(f"Error processing unban user ID: {e}")
        await message.reply_text(f"Error: {str(e)}")

@Client.on_callback_query(filters.regex("^back_to_ban_panel$") & filters.user(ADMIN_USER_ID))
async def back_to_ban_panel(client: Client, callback_query):
    """Return to main ban panel"""
    # Clean up any waiting state
    user_id = callback_query.from_user.id
    if user_id in ban_waiting_for_user_id:
        del ban_waiting_for_user_id[user_id]
    
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

@Client.on_callback_query(filters.regex("^close_ban_panel$") & filters.user(ADMIN_USER_ID))
async def close_ban_panel(client: Client, callback_query):
    """Close the ban control panel"""
    # Clean up any waiting state
    user_id = callback_query.from_user.id
    if user_id in ban_waiting_for_user_id:
        del ban_waiting_for_user_id[user_id]
    
    await callback_query.message.delete()
    await callback_query.answer("Ban panel closed")

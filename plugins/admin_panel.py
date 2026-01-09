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
            
            # Check if user is banned
            ban_status = user.get('ban_status', {})
            if ban_status.get('is_banned', False):
                # Skip banned users
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

# =====================================================
# BAN SYSTEM IMPLEMENTATION
# =====================================================

async def is_user_banned(user_id):
    """Check if a user is banned"""
    try:
        user = await n4bots.col.find_one({"_id": int(user_id)})
        if user and 'ban_status' in user:
            ban_status = user['ban_status']
            if ban_status.get('is_banned', False):
                # Check if temporary ban has expired
                ban_duration = ban_status.get('ban_duration', 0)
                banned_on = ban_status.get('banned_on')
                
                if ban_duration > 0 and banned_on:
                    try:
                        # Parse the date string
                        banned_date = datetime.datetime.strptime(banned_on, "%Y-%m-%d").date()
                        current_date = datetime.date.today()
                        
                        # Calculate days difference
                        days_banned = (current_date - banned_date).days
                        
                        # If temporary ban has expired, auto-unban
                        if days_banned >= ban_duration:
                            await unban_user(user_id, auto=True)
                            return False
                    except Exception as e:
                        logger.error(f"Error checking ban expiration for user {user_id}: {e}")
                        return True
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking ban status for user {user_id}: {e}")
        return False

async def ban_user(user_id, duration_days=0, reason="Banned by admin"):
    """Ban a user"""
    try:
        ban_status = {
            "is_banned": True,
            "ban_duration": duration_days,
            "banned_on": datetime.date.today().isoformat(),
            "ban_reason": reason
        }
        
        await n4bots.col.update_one(
            {"_id": int(user_id)},
            {"$set": {"ban_status": ban_status}},
            upsert=True
        )
        
        # Send ban notification to user
        try:
            await bot.send_message(
                int(user_id),
                f"🚫 You are banned from using this bot.\n\n"
                f"**Reason:** {reason}\n"
                f"**Duration:** {'Permanent' if duration_days == 0 else f'{duration_days} days'}\n"
                f"**Banned on:** {datetime.date.today().isoformat()}\n\n"
                f"Contact @Animelibraryn4 if you believe this is a mistake."
            )
        except Exception as e:
            logger.error(f"Failed to send ban message to user {user_id}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error banning user {user_id}: {e}")
        return False

async def unban_user(user_id, auto=False):
    """Unban a user"""
    try:
        ban_status = {
            "is_banned": False,
            "ban_duration": 0,
            "banned_on": datetime.date.max.isoformat(),
            "ban_reason": ''
        }
        
        await n4bots.col.update_one(
            {"_id": int(user_id)},
            {"$set": {"ban_status": ban_status}}
        )
        
        # Send unban notification to user if not auto-unban
        if not auto:
            try:
                await bot.send_message(
                    int(user_id),
                    "✅ **Your ban has been lifted!**\n\n"
                    "You can now use the bot again. Welcome back!"
                )
            except Exception as e:
                logger.error(f"Failed to send unban message to user {user_id}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error unbanning user {user_id}: {e}")
        return False

async def get_banned_users():
    """Get list of all banned users"""
    try:
        banned_users = []
        async for user in n4bots.col.find({"ban_status.is_banned": True}):
            ban_status = user.get('ban_status', {})
            banned_users.append({
                "user_id": user['_id'],
                "banned_on": ban_status.get('banned_on', 'Unknown'),
                "duration": ban_status.get('ban_duration', 0),
                "reason": ban_status.get('ban_reason', 'No reason provided')
            })
        return banned_users
    except Exception as e:
        logger.error(f"Error getting banned users: {e}")
        return []

@Client.on_message(filters.command("ban") & filters.user(Config.ADMIN))
async def ban_command(bot: Client, message: Message):
    """Ban a user permanently or temporarily"""
    if len(message.command) < 2:
        await message.reply_text(
            "**Usage:** `/ban <user_id> <reason>`\n\n"
            "**Example:** `/ban 123456789 Violating rules`\n"
            "**Example for temporary ban:** `/ban 123456789 7 Spamming` (7 days)"
        )
        return
    
    try:
        # Parse command arguments
        args = message.text.split()
        
        if len(args) == 2:
            # Permanent ban: /ban <user_id>
            user_id = int(args[1])
            reason = "Banned by admin"
            duration = 0
        elif len(args) >= 3:
            # Check if second argument is a number (duration)
            if args[2].isdigit():
                # Temporary ban: /ban <user_id> <days> <reason>
                user_id = int(args[1])
                duration = int(args[2])
                reason = " ".join(args[3:]) if len(args) > 3 else "Banned by admin"
            else:
                # Permanent ban with reason: /ban <user_id> <reason>
                user_id = int(args[1])
                reason = " ".join(args[2:])
                duration = 0
        else:
            await message.reply_text("Invalid command format.")
            return
        
        # Check if user exists in database
        user_exists = await n4bots.is_user_exist(user_id)
        if not user_exists:
            await message.reply_text(f"User `{user_id}` not found in database.")
            return
        
        # Check if already banned
        if await is_user_banned(user_id):
            await message.reply_text(f"User `{user_id}` is already banned.")
            return
        
        # Ban the user
        success = await ban_user(user_id, duration, reason)
        
        if success:
            duration_text = f"{duration} days" if duration > 0 else "Permanent"
            await message.reply_text(
                f"✅ **User banned successfully!**\n\n"
                f"**User ID:** `{user_id}`\n"
                f"**Duration:** {duration_text}\n"
                f"**Reason:** {reason}"
            )
            
            # Log to admin channel
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"🚫 **User Banned**\n\n"
                    f"**Admin:** {message.from_user.mention}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Duration:** {duration_text}\n"
                    f"**Reason:** {reason}\n"
                    f"**Date:** {datetime.date.today().isoformat()}"
                )
            except:
                pass
        else:
            await message.reply_text("Failed to ban user. Please check logs.")
            
    except ValueError:
        await message.reply_text("Invalid user ID. Please provide a valid numeric user ID.")
    except Exception as e:
        logger.error(f"Error in ban command: {e}")
        await message.reply_text(f"An error occurred: {str(e)}")

@Client.on_message(filters.command("tban") & filters.user(Config.ADMIN))
async def tban_command(bot: Client, message: Message):
    """Temporary ban with minutes/hours/days specification"""
    if len(message.command) < 4:
        await message.reply_text(
            "**Usage:** `/tban <user_id> <time> <reason>`\n\n"
            "**Time formats:**\n"
            "• `30m` - 30 minutes\n"
            "• `2h` - 2 hours\n"
            "• `7d` - 7 days\n\n"
            "**Examples:**\n"
            "`/tban 123456789 30m Spamming`\n"
            "`/tban 123456789 2h Flooding`\n"
            "`/tban 123456789 7d Violating rules`"
        )
        return
    
    try:
        user_id = int(message.command[1])
        time_str = message.command[2].lower()
        reason = " ".join(message.command[3:]) if len(message.command) > 3 else "Temporarily banned by admin"
        
        # Parse time duration
        duration_days = 0
        
        if time_str.endswith('m'):
            # Minutes to days (1 day = 1440 minutes)
            minutes = int(time_str[:-1])
            duration_days = minutes / 1440
        elif time_str.endswith('h'):
            # Hours to days
            hours = int(time_str[:-1])
            duration_days = hours / 24
        elif time_str.endswith('d'):
            # Days
            duration_days = int(time_str[:-1])
        else:
            # Assume days if no unit specified
            duration_days = int(time_str)
        
        # Convert to integer days (minimum 1 day for consistency)
        duration_days = max(1, int(duration_days))
        
        # Check if user exists
        user_exists = await n4bots.is_user_exist(user_id)
        if not user_exists:
            await message.reply_text(f"User `{user_id}` not found in database.")
            return
        
        # Check if already banned
        if await is_user_banned(user_id):
            await message.reply_text(f"User `{user_id}` is already banned.")
            return
        
        # Ban the user
        success = await ban_user(user_id, duration_days, reason)
        
        if success:
            # Format duration for display
            if time_str.endswith('m'):
                duration_display = f"{int(time_str[:-1])} minutes"
            elif time_str.endswith('h'):
                duration_display = f"{int(time_str[:-1])} hours"
            else:
                duration_display = f"{duration_days} days"
            
            await message.reply_text(
                f"✅ **User temporarily banned!**\n\n"
                f"**User ID:** `{user_id}`\n"
                f"**Duration:** {duration_display}\n"
                f"**Reason:** {reason}"
            )
            
            # Log to admin channel
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"⏳ **User Temporarily Banned**\n\n"
                    f"**Admin:** {message.from_user.mention}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Duration:** {duration_display}\n"
                    f"**Reason:** {reason}\n"
                    f"**Date:** {datetime.date.today().isoformat()}"
                )
            except:
                pass
        else:
            await message.reply_text("Failed to ban user. Please check logs.")
            
    except ValueError:
        await message.reply_text("Invalid input. Please check the command format.")
    except Exception as e:
        logger.error(f"Error in tban command: {e}")
        await message.reply_text(f"An error occurred: {str(e)}")

@Client.on_message(filters.command("unban") & filters.user(Config.ADMIN))
async def unban_command(bot: Client, message: Message):
    """Unban a user"""
    if len(message.command) != 2:
        await message.reply_text("**Usage:** `/unban <user_id>`\n\n**Example:** `/unban 123456789`")
        return
    
    try:
        user_id = int(message.command[1])
        
        # Check if user exists
        user_exists = await n4bots.is_user_exist(user_id)
        if not user_exists:
            await message.reply_text(f"User `{user_id}` not found in database.")
            return
        
        # Check if user is actually banned
        if not await is_user_banned(user_id):
            await message.reply_text(f"User `{user_id}` is not banned.")
            return
        
        # Unban the user
        success = await unban_user(user_id)
        
        if success:
            await message.reply_text(f"✅ **User unbanned successfully!**\n\n**User ID:** `{user_id}`")
            
            # Log to admin channel
            try:
                await bot.send_message(
                    Config.LOG_CHANNEL,
                    f"✅ **User Unbanned**\n\n"
                    f"**Admin:** {message.from_user.mention}\n"
                    f"**User ID:** `{user_id}`\n"
                    f"**Date:** {datetime.date.today().isoformat()}"
                )
            except:
                pass
        else:
            await message.reply_text("Failed to unban user. Please check logs.")
            
    except ValueError:
        await message.reply_text("Invalid user ID. Please provide a valid numeric user ID.")
    except Exception as e:
        logger.error(f"Error in unban command: {e}")
        await message.reply_text(f"An error occurred: {str(e)}")

@Client.on_message(filters.command("banlist") & filters.user(Config.ADMIN))
async def banlist_command(bot: Client, message: Message):
    """Show list of banned users"""
    try:
        banned_users = await get_banned_users()
        
        if not banned_users:
            await message.reply_text("📋 **No banned users found.**")
            return
        
        # Format the list
        ban_list_text = "🚫 **Banned Users List**\n\n"
        
        for i, user in enumerate(banned_users, 1):
            duration = "Permanent" if user['duration'] == 0 else f"{user['duration']} days"
            ban_list_text += (
                f"**{i}. User ID:** `{user['user_id']}`\n"
                f"   **Banned on:** {user['banned_on']}\n"
                f"   **Duration:** {duration}\n"
                f"   **Reason:** {user['reason']}\n\n"
            )
        
        # Add summary
        ban_list_text += f"**Total banned users:** {len(banned_users)}"
        
        # Send as multiple messages if too long
        if len(ban_list_text) > 4000:
            chunks = [ban_list_text[i:i+4000] for i in range(0, len(ban_list_text), 4000)]
            for chunk in chunks:
                await message.reply_text(chunk)
        else:
            await message.reply_text(ban_list_text)
            
    except Exception as e:
        logger.error(f"Error in banlist command: {e}")
        await message.reply_text(f"An error occurred: {str(e)}")

# =====================================================
# BAN CHECK INTEGRATION
# =====================================================

# This function should be called before processing any user command
async def check_ban_status(user_id):
    """Check if user is banned before processing commands"""
    return await is_user_banned(user_id)
        
     

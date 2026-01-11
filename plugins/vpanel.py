from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from helper.database import n4bots
from config import Config
import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Vpanel.py file successfully loaded!") # Ye bot start hote hi terminal mein aana chahiye

@Client.on_message(filters.text & filters.private)
async def echo(client, message):
    if message.text == "/vpanel":
        await message.reply_text("Manual check: Vpanel command detected!")
        
    
@Client.on_message(filters.command("vpanel") & filters.user(Config.ADMIN) & filters.reply)
async def vpanel_command(bot: Client, m: Message):
    """Main verification panel"""
    try:
        buttons = [
            [InlineKeyboardButton("⚙️ Verification Settings", callback_data="vpanel_settings")],
            [InlineKeyboardButton("⭐ Premium Management", callback_data="vpanel_premium")],
            [InlineKeyboardButton("📊 Statistics", callback_data="vpanel_stats")],
            [InlineKeyboardButton("❌ Close", callback_data="vpanel_close")]
        ]
        
        await message.reply_text(
            "**🔐 Verification & Premium Control Panel**\n\n"
            "Control all bot settings directly from Telegram:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        logger.info(f"Admin {message.from_user.id} opened vpanel")
    except Exception as e:
        logger.error(f"Error in vpanel_command: {e}")
        await message.reply_text(f"❌ Error: {e}")

# =====================================================
# MAIN CALLBACK HANDLER
# =====================================================

@Client.on_callback_query(filters.regex(r"^vpanel_"))
async def vpanel_callback_handler(client, query: CallbackQuery):
    data = query.data
    logger.info(f"Callback received: {data} from user {query.from_user.id}")
    
    try:
        if data == "vpanel_settings":
            await show_verification_settings(client, query)
        elif data == "vpanel_premium":
            await show_premium_management(client, query)
        elif data == "vpanel_stats":
            await show_statistics(client, query)
        elif data == "vpanel_close":
            await query.message.delete()
        elif data == "vpanel_main":
            # Return to main panel
            buttons = [
                [InlineKeyboardButton("⚙️ Verification Settings", callback_data="vpanel_settings")],
                [InlineKeyboardButton("⭐ Premium Management", callback_data="vpanel_premium")],
                [InlineKeyboardButton("📊 Statistics", callback_data="vpanel_stats")],
                [InlineKeyboardButton("❌ Close", callback_data="vpanel_close")]
            ]
            await query.message.edit_text(
                "**🔐 Verification & Premium Control Panel**\n\n"
                "Control all bot settings directly from Telegram:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await query.answer("❌ Unknown command", show_alert=True)
    except Exception as e:
        logger.error(f"Error in vpanel_callback_handler: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

# =====================================================
# VERIFICATION SETTINGS
# =====================================================

async def show_verification_settings(client, query):
    """Show verification settings"""
    try:
        settings = await n4bots.get_bot_settings()
        
        # Format expiry time
        expiry_seconds = settings.get('verify_expire', 30000)
        hours = expiry_seconds // 3600
        minutes = (expiry_seconds % 3600) // 60
        
        text = f"""
**⚙️ Verification Settings**

🔹 **Status:** {'✅ Enabled' if settings.get('verify_enabled', True) else '❌ Disabled'}
🔹 **Expiry:** {hours}h {minutes}m ({expiry_seconds} seconds)
🔹 **Shortlink Site:** {settings.get('shortlink_site', 'gplinks.com')}
🔹 **Tutorial:** {settings.get('verify_tutorial', 'Not set')}
🔹 **API Key:** {'✅ Set' if settings.get('shortlink_api') else '❌ Not set'}

*Last Updated:* {settings.get('updated_at', datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        buttons = [
            [
                InlineKeyboardButton("✅ Enable" if not settings.get('verify_enabled', True) else "❌ Disable", 
                                   callback_data=f"toggle_verify_{'off' if settings.get('verify_enabled', True) else 'on'}"),
                InlineKeyboardButton("🕐 Change Expiry", callback_data="change_expiry")
            ],
            [
                InlineKeyboardButton("🔗 Change Shortlink", callback_data="change_shortlink"),
                InlineKeyboardButton("📚 Change Tutorial", callback_data="change_tutorial")
            ],
            [
                InlineKeyboardButton("🖼️ Change Image", callback_data="change_image"),
                InlineKeyboardButton("🔑 Change API", callback_data="change_api_key")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_main")]
        ]
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        logger.error(f"Error in show_verification_settings: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

# =====================================================
# PREMIUM MANAGEMENT
# =====================================================

async def show_premium_management(client, query):
    """Show premium management interface"""
    try:
        buttons = [
            [InlineKeyboardButton("➕ Add Premium User", callback_data="premium_add")],
            [InlineKeyboardButton("➖ Remove Premium User", callback_data="premium_remove")],
            [InlineKeyboardButton("📋 List Premium Users", callback_data="premium_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_main")]
        ]
        
        await query.message.edit_text(
            "**⭐ Premium User Management**\n\n"
            "Add, remove, or list premium users:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Error in show_premium_management: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

# =====================================================
# STATISTICS
# =====================================================

async def show_statistics(client, query):
    """Show bot statistics"""
    try:
        total_users = await n4bots.total_users_count()
        premium_users = await n4bots.get_premium_users()
        premium_count = len(premium_users)
        
        # Calculate verification rate
        verified_count = 0
        async for user in n4bots.col.find({}):
            if user.get("verify_status", 0) > 0:
                verified_count += 1
        
        verification_rate = (verified_count / total_users * 100) if total_users > 0 else 0
        
        text = f"""
**📊 Bot Statistics**

👥 **Total Users:** {total_users}
✅ **Verified Users:** {verified_count}
⭐ **Premium Users:** {premium_count}
📈 **Verification Rate:** {verification_rate:.1f}%

**Recent Premium Users:**
"""
        
        # Add last 5 premium users
        for i, user in enumerate(premium_users[:5], 1):
            user_id = user.get('user_id', 'N/A')
            expires = user.get('expires_at', 'Lifetime')
            if isinstance(expires, datetime.datetime):
                expires = expires.strftime('%Y-%m-%d')
            text += f"{i}. User ID: `{user_id}` - Expires: {expires}\n"
        
        if len(premium_users) > 5:
            text += f"\n... and {len(premium_users) - 5} more"
        
        buttons = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="vpanel_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_main")]
        ]
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        logger.error(f"Error in show_statistics: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

# =====================================================
# PREMIUM ADD HANDLERS
# =====================================================

@Client.on_callback_query(filters.regex(r"^premium_add$"))
async def premium_add_handler(client, query: CallbackQuery):
    """Start premium user addition"""
    try:
        await query.message.edit_text(
            "**➕ Add Premium User**\n\n"
            "Please send me the user's Telegram ID.\n"
            "You can get it using @userinfobot\n\n"
            "Send: `/add_premium 1234567890`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="vpanel_premium")]
            ])
        )
    except Exception as e:
        logger.error(f"Error in premium_add_handler: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.command("add_premium"))
async def handle_add_premium_command(client, message: Message):
    """Handle add premium command"""
    try:
        if len(message.command) != 2:
            await message.reply_text("❌ Usage: `/add_premium user_id`")
            return
        
        target_user_id = int(message.command[1])
        
        # Show duration options
        buttons = [
            [InlineKeyboardButton("⏰ 10 Minutes", callback_data=f"premium_duration_{target_user_id}_10m")],
            [InlineKeyboardButton("🕐 1 Hour", callback_data=f"premium_duration_{target_user_id}_1h")],
            [InlineKeyboardButton("📅 1 Day", callback_data=f"premium_duration_{target_user_id}_1d")],
            [InlineKeyboardButton("📆 7 Days", callback_data=f"premium_duration_{target_user_id}_7d")],
            [InlineKeyboardButton("📅 30 Days", callback_data=f"premium_duration_{target_user_id}_30d")],
            [InlineKeyboardButton("∞ Lifetime", callback_data=f"premium_duration_{target_user_id}_0")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="vpanel_premium")]
        ]
        
        await message.reply_text(
            f"**Select duration for user ID:** `{target_user_id}`",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please send a numeric ID.")
    except Exception as e:
        logger.error(f"Error in handle_add_premium_command: {e}")
        await message.reply_text(f"❌ Error: {e}")

# =====================================================
# PREMIUM DURATION HANDLER
# =====================================================

@Client.on_callback_query(filters.regex(r"^premium_duration_"))
async def handle_premium_duration(client, query: CallbackQuery):
    """Handle premium duration selection"""
    try:
        parts = query.data.split("_")
        target_user_id = int(parts[2])
        duration_str = parts[3]
        
        # Convert duration to days
        duration_map = {
            "10m": (0.007, "10 minutes"),
            "1h": (0.042, "1 hour"),
            "1d": (1, "1 day"),
            "7d": (7, "7 days"),
            "30d": (30, "30 days"),
            "0": (0, "Lifetime")
        }
        
        if duration_str not in duration_map:
            await query.answer("❌ Invalid duration", show_alert=True)
            return
        
        duration_days, readable = duration_map[duration_str]
        
        # Add premium user
        success = await n4bots.add_premium_user(
            target_user_id, 
            duration_days, 
            query.from_user.id
        )
        
        if success:
            if duration_days == 0:
                expiry_text = "Never (Lifetime)"
            else:
                expiry_date = datetime.datetime.now() + datetime.timedelta(days=duration_days)
                expiry_text = expiry_date.strftime("%Y-%m-%d %H:%M:%S")
            
            await query.message.edit_text(
                f"✅ **Premium User Added Successfully!**\n\n"
                f"**User ID:** `{target_user_id}`\n"
                f"**Duration:** {readable}\n"
                f"**Expires:** {expiry_text}\n\n"
                f"*Added by:* {query.from_user.mention}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="vpanel_premium")]
                ])
            )
            
            # Notify the user if possible
            try:
                await client.send_message(
                    target_user_id,
                    f"🎉 **You've been granted premium access!**\n\n"
                    f"**Duration:** {readable}\n"
                    f"**Expires:** {expiry_text}\n\n"
                    f"Enjoy premium features! 🚀"
                )
            except Exception as e:
                logger.warning(f"Could not notify user {target_user_id}: {e}")
        else:
            await query.answer("❌ Failed to add premium user", show_alert=True)
    except Exception as e:
        logger.error(f"Error in handle_premium_duration: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

# =====================================================
# PREMIUM LIST HANDLER
# =====================================================

@Client.on_callback_query(filters.regex(r"^premium_list$"))
async def premium_list_handler(client, query: CallbackQuery):
    """List all premium users"""
    try:
        premium_users = await n4bots.get_premium_users()
        
        if not premium_users:
            text = "**📋 Premium Users List**\n\nNo premium users found."
        else:
            text = "**📋 Premium Users List**\n\n"
            for i, user in enumerate(premium_users, 1):
                user_id = user.get('user_id', 'N/A')
                added_by = user.get('added_by', 'Unknown')
                added_at = user.get('added_at', datetime.datetime.now())
                expires = user.get('expires_at', 'Lifetime')
                
                if isinstance(added_at, datetime.datetime):
                    added_at_str = added_at.strftime('%Y-%m-%d')
                else:
                    added_at_str = str(added_at)
                
                if isinstance(expires, datetime.datetime):
                    expires_str = expires.strftime('%Y-%m-%d')
                    days_left = (expires - datetime.datetime.now()).days
                    expires_text = f"{expires_str} ({days_left} days left)"
                else:
                    expires_text = "Lifetime"
                
                text += f"{i}. `{user_id}`\n"
                text += f"   Added: {added_at_str}\n"
                text += f"   Expires: {expires_text}\n"
                text += f"   Added by: {added_by}\n\n"
        
        buttons = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="premium_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_premium")]
        ]
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error in premium_list_handler: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

# =====================================================
# PREMIUM REMOVE HANDLERS
# =====================================================

@Client.on_callback_query(filters.regex(r"^premium_remove$"))
async def premium_remove_handler(client, query: CallbackQuery):
    """Start premium user removal"""
    try:
        await query.message.edit_text(
            "**➖ Remove Premium User**\n\n"
            "Please send me the user's Telegram ID to remove premium access.\n\n"
            "Send: `/remove_premium 1234567890`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="vpanel_premium")]
            ])
        )
    except Exception as e:
        logger.error(f"Error in premium_remove_handler: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.command("remove_premium"))
async def handle_remove_premium_command(client, message: Message):
    """Handle premium removal command"""
    try:
        if len(message.command) != 2:
            await message.reply_text("❌ Usage: `/remove_premium user_id`")
            return
        
        target_user_id = int(message.command[1])
        
        # Check if user is premium
        is_premium = await n4bots.is_user_premium(target_user_id)
        if not is_premium:
            await message.reply_text(f"❌ User `{target_user_id}` is not a premium user.")
            return
        
        # Remove premium
        success = await n4bots.remove_premium_user(target_user_id)
        
        if success:
            await message.reply_text(f"✅ Premium access removed from user `{target_user_id}`")
            
            # Notify user if possible
            try:
                await client.send_message(
                    target_user_id,
                    "⚠️ **Your premium access has been removed.**\n\n"
                    "You can purchase premium again or use free verification."
                )
            except Exception as e:
                logger.warning(f"Could not notify user {target_user_id}: {e}")
        else:
            await message.reply_text(f"❌ Failed to remove premium from user `{target_user_id}`")
    
    except ValueError:
        await message.reply_text("❌ Invalid user ID. Please send a numeric ID.")
    except Exception as e:
        logger.error(f"Error in handle_remove_premium_command: {e}")
        await message.reply_text(f"❌ Error: {e}")

# =====================================================
# TOGGLE VERIFICATION HANDLER
# =====================================================

@Client.on_callback_query(filters.regex(r"^toggle_verify_"))
async def toggle_verify_handler(client, query: CallbackQuery):
    """Toggle verification on/off"""
    try:
        action = query.data.split("_")[2]  # on or off
        
        settings = await n4bots.get_bot_settings()
        current_status = settings.get("verify_enabled", True)
        
        # If already in the requested state, do nothing
        if (action == "on" and current_status) or (action == "off" and not current_status):
            await query.answer("Already in that state!", show_alert=True)
            return
        
        success = await n4bots.update_bot_settings({
            "verify_enabled": action == "on"
        })
        
        if success:
            status_text = "✅ Verification ENABLED" if action == "on" else "❌ Verification DISABLED"
            await query.answer(f"{status_text}", show_alert=True)
            await show_verification_settings(client, query)
        else:
            await query.answer("❌ Failed to update settings", show_alert=True)
    except Exception as e:
        logger.error(f"Error in toggle_verify_handler: {e}")
        await query.answer(f"❌ Error: {e}", show_alert=True)

# =====================================================
# SETTINGS CHANGE HANDLERS (PLACEHOLDERS)
# =====================================================

@Client.on_callback_query(filters.regex(r"^change_"))
async def change_settings_handler(client, query: CallbackQuery):
    """Handle settings change requests"""
    setting_type = query.data.replace("change_", "")
    
    messages = {
        "expiry": "Send the expiry time in seconds (e.g., 3600 for 1 hour, 86400 for 1 day):",
        "shortlink": "Send the new shortlink site (e.g., gplinks.in, ouo.io):",
        "tutorial": "Send the new tutorial URL:",
        "image": "Send the new verification image URL:",
        "api_key": "Send the new shortlink API key:"
    }
    
    if setting_type in messages:
        await query.message.edit_text(
            f"**Change {setting_type.replace('_', ' ').title()}**\n\n{messages[setting_type]}\n\n"
            f"Send: `/set_{setting_type} value`\n"
            f"Example: `/set_{setting_type} new_value`",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="vpanel_settings")]
            ])
        )
    else:
        await query.answer("❌ Unknown setting", show_alert=True)

# =====================================================
# SETTINGS COMMANDS
# =====================================================

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.command("set_expiry"))
async def set_expiry_command(client, message: Message):
    """Set verification expiry time"""
    try:
        if len(message.command) != 2:
            await message.reply_text("❌ Usage: `/set_expiry seconds`")
            return
        
        seconds = int(message.command[1])
        if seconds < 60:
            await message.reply_text("❌ Expiry must be at least 60 seconds")
            return
        
        success = await n4bots.update_bot_settings({
            "verify_expire": seconds
        })
        
        if success:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            await message.reply_text(f"✅ Expiry set to {hours}h {minutes}m ({seconds} seconds)")
        else:
            await message.reply_text("❌ Failed to update expiry")
    except ValueError:
        await message.reply_text("❌ Invalid number. Please send numeric value.")
    except Exception as e:
        logger.error(f"Error in set_expiry_command: {e}")
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.command("set_shortlink"))
async def set_shortlink_command(client, message: Message):
    """Set shortlink site"""
    try:
        if len(message.command) != 2:
            await message.reply_text("❌ Usage: `/set_shortlink site.com`")
            return
        
        site = message.command[1]
        success = await n4bots.update_bot_settings({
            "shortlink_site": site
        })
        
        if success:
            await message.reply_text(f"✅ Shortlink site set to {site}")
        else:
            await message.reply_text("❌ Failed to update shortlink site")
    except Exception as e:
        logger.error(f"Error in set_shortlink_command: {e}")
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.command("set_tutorial"))
async def set_tutorial_command(client, message: Message):
    """Set tutorial URL"""
    try:
        if len(message.command) != 2:
            await message.reply_text("❌ Usage: `/set_tutorial https://example.com`")
            return
        
        url = message.command[1]
        success = await n4bots.update_bot_settings({
            "verify_tutorial": url
        })
        
        if success:
            await message.reply_text(f"✅ Tutorial URL set to {url}")
        else:
            await message.reply_text("❌ Failed to update tutorial URL")
    except Exception as e:
        logger.error(f"Error in set_tutorial_command: {e}")
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.command("set_image"))
async def set_image_command(client, message: Message):
    """Set verification image"""
    try:
        if len(message.command) != 2:
            await message.reply_text("❌ Usage: `/set_image https://example.com/image.jpg`")
            return
        
        image_url = message.command[1]
        success = await n4bots.update_bot_settings({
            "verify_photo": image_url
        })
        
        if success:
            await message.reply_text(f"✅ Verification image set to {image_url}")
        else:
            await message.reply_text("❌ Failed to update verification image")
    except Exception as e:
        logger.error(f"Error in set_image_command: {e}")
        await message.reply_text(f"❌ Error: {e}")

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.command("set_api_key"))
async def set_api_key_command(client, message: Message):
    """Set shortlink API key"""
    try:
        if len(message.command) != 2:
            await message.reply_text("❌ Usage: `/set_api_key your_api_key`")
            return
        
        api_key = message.command[1]
        success = await n4bots.update_bot_settings({
            "shortlink_api": api_key
        })
        
        if success:
            await message.reply_text("✅ API key updated successfully")
        else:
            await message.reply_text("❌ Failed to update API key")
    except Exception as e:
        logger.error(f"Error in set_api_key_command: {e}")
        await message.reply_text(f"❌ Error: {e}")

# =====================================================
# TEST COMMAND
# =====================================================

@Client.on_message(filters.command("test_vpanel") & filters.user(Config.ADMIN))
async def test_vpanel(client, message):
    """Test vpanel functionality"""
    try:
        # Test database connection
        settings = await n4bots.get_bot_settings()
        await message.reply_text(f"✅ Database connected. Settings: {settings.get('verify_enabled', 'N/A')}")
        
        # Test premium functions
        premium_count = len(await n4bots.get_premium_users())
        await message.reply_text(f"✅ Premium users count: {premium_count}")
        
    except Exception as e:
        await message.reply_text(f"❌ Test failed: {e}")

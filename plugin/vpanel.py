from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from helper.database import n4bots
from config import Config
import datetime

@Client.on_message(filters.command("vpanel") & filters.user(Config.ADMIN))
async def vpanel_command(client, message):
    """Main verification panel"""
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

@Client.on_callback_query(filters.regex(r"^vpanel_"))
async def vpanel_callback_handler(client, query: CallbackQuery):
    data = query.data
    
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

async def show_verification_settings(client, query):
    """Show verification settings"""
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
            InlineKeyboardButton("🔑 Change API Key", callback_data="change_api")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="vpanel_main")]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def show_premium_management(client, query):
    """Show premium management interface"""
    buttons = [
        [InlineKeyboardButton("➕ Add Premium User", callback_data="premium_add")],
        [InlineKeyboardButton("➖ Remove Premium User", callback_data="premium_remove")],
        [InlineKeyboardButton("📋 List Premium Users", callback_data="premium_list")],
        [InlineKeyboardButton("🎁 Free Trial Settings", callback_data="premium_trial")],
        [InlineKeyboardButton("🔙 Back", callback_data="vpanel_main")]
    ]
    
    await query.message.edit_text(
        "**⭐ Premium User Management**\n\n"
        "Add, remove, or list premium users:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

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
        
        text = f"""
**📊 Bot Statistics**

👥 **Total Users:** {total_users}
✅ **Verified Users:** {verified_count}
⭐ **Premium Users:** {premium_count}
📈 **Verification Rate:** {(verified_count/total_users*100) if total_users > 0 else 0:.1f}%

**Premium Users (Last 10):**
"""
        
        # Add last 10 premium users
        for i, user in enumerate(premium_users[:10], 1):
            user_id = user.get('user_id', 'N/A')
            expires = user.get('expires_at', 'Lifetime')
            if isinstance(expires, datetime.datetime):
                expires = expires.strftime('%Y-%m-%d')
            text += f"{i}. User ID: `{user_id}` - Expires: {expires}\n"
        
        if len(premium_users) > 10:
            text += f"\n... and {len(premium_users) - 10} more"
        
    except Exception as e:
        text = f"**📊 Bot Statistics**\n\nError loading statistics: {e}"
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="vpanel_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_main")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^premium_add$"))
async def premium_add_handler(client, query):
    """Start premium user addition"""
    await query.message.edit_text(
        "**➕ Add Premium User**\n\n"
        "Send me the user's Telegram ID.\n"
        "You can get it with @userinfobot\n\n"
        "Format: `/premium_add 1234567890`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_premium")]
        ])
    )
    
    # Store that we're waiting for user input
    user_id = query.from_user.id
    await n4bots.col.update_one(
        {"_id": user_id},
        {"$set": {"awaiting_premium_user": True}}
    )

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.regex(r"^\d+$"))
async def handle_premium_user_input(client, message):
    """Handle premium user ID input"""
    user_data = await n4bots.col.find_one({"_id": message.from_user.id})
    
    if user_data and user_data.get("awaiting_premium_user"):
        target_user_id = int(message.text)
        
        # Clear awaiting flag
        await n4bots.col.update_one(
            {"_id": message.from_user.id},
            {"$unset": {"awaiting_premium_user": ""}}
        )
        
        # Check if user exists
        if not await n4bots.is_user_exist(target_user_id):
            await message.reply_text(
                f"⚠️ User `{target_user_id}` not found in database.\n"
                f"User needs to start the bot first.\n\n"
                f"Do you want to add them anyway?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Yes", callback_data=f"force_premium_{target_user_id}")],
                    [InlineKeyboardButton("❌ No", callback_data="vpanel_premium")]
                ])
            )
            return
        
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

@Client.on_callback_query(filters.regex(r"^force_premium_"))
async def handle_force_premium(client, query):
    """Handle force premium addition for non-existing user"""
    target_user_id = int(query.data.split("_")[2])
    
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
    
    await query.message.edit_text(
        f"**User will be created automatically.**\n"
        f"**Select duration for user ID:** `{target_user_id}`",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^premium_duration_"))
async def handle_premium_duration(client, query):
    """Handle premium duration selection"""
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
        except:
            pass
    else:
        await query.answer("❌ Failed to add premium user", show_alert=True)

@Client.on_callback_query(filters.regex(r"^toggle_verify_"))
async def toggle_verify_handler(client, query):
    """Toggle verification on/off"""
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

@Client.on_callback_query(filters.regex(r"^premium_list$"))
async def premium_list_handler(client, query):
    """List all premium users"""
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
            
            if isinstance(expires, datetime.datetime):
                expires_str = expires.strftime('%Y-%m-%d')
                days_left = (expires - datetime.datetime.now()).days
                expires_text = f"{expires_str} ({days_left} days left)"
            else:
                expires_text = "Lifetime"
            
            text += f"{i}. `{user_id}`\n"
            text += f"   Added: {added_at.strftime('%Y-%m-%d')}\n"
            text += f"   Expires: {expires_text}\n\n"
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="premium_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_premium")]
        ]),
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^premium_remove$"))
async def premium_remove_handler(client, query):
    """Start premium user removal"""
    await query.message.edit_text(
        "**➖ Remove Premium User**\n\n"
        "Send me the user's Telegram ID to remove premium access.\n\n"
        "Format: `/premium_remove 1234567890`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_premium")]
        ])
    )
    
    # Store that we're waiting for removal input
    user_id = query.from_user.id
    await n4bots.col.update_one(
        {"_id": user_id},
        {"$set": {"awaiting_premium_remove": True}}
    )

@Client.on_message(filters.private & filters.user(Config.ADMIN) & filters.regex(r"^/premium_remove \d+$"))
async def handle_premium_remove_command(client, message):
    """Handle premium removal command"""
    try:
        target_user_id = int(message.text.split()[1])
        
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
            except:
                pass
        else:
            await message.reply_text(f"❌ Failed to remove premium from user `{target_user_id}`")
    
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

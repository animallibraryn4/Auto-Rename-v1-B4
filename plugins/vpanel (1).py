from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from helper.database import n4bots
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

async def show_verification_settings(client, query):
    """Show verification settings"""
    settings = await n4bots.get_bot_settings()
    
    text = f"""
**⚙️ Verification Settings**

🔹 **Status:** {'✅ Enabled' if settings['verify_enabled'] else '❌ Disabled'}
🔹 **Expiry:** {settings['verify_expire']} seconds
🔹 **Shortlink Site:** {settings['shortlink_site']}
🔹 **Tutorial:** {settings['verify_tutorial']}

*Last Updated:* {settings['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    buttons = [
        [
            InlineKeyboardButton("✅ Enable" if not settings['verify_enabled'] else "❌ Disable", 
                               callback_data=f"toggle_verify_{'off' if settings['verify_enabled'] else 'on'}"),
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
        [InlineKeyboardButton("🎁 Free Trial", callback_data="premium_trial")],
        [InlineKeyboardButton("🔙 Back", callback_data="vpanel_main")]
    ]
    
    await query.message.edit_text(
        "**⭐ Premium User Management**\n\n"
        "Add, remove, or list premium users:",
        reply_markup=InlineKeyboardMarkup(buttons)
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
        
        # Show duration options
        buttons = [
            [InlineKeyboardButton("⏰ 10 Minutes", callback_data=f"premium_duration_{target_user_id}_10m")],
            [InlineKeyboardButton("🕐 1 Hour", callback_data=f"premium_duration_{target_user_id}_1h")],
            [InlineKeyboardButton("📅 1 Day", callback_data=f"premium_duration_{target_user_id}_1d")],
            [InlineKeyboardButton("📆 7 Days", callback_data=f"premium_duration_{target_user_id}_7d")],
            [InlineKeyboardButton("∞ Lifetime", callback_data=f"premium_duration_{target_user_id}_0")],
            [InlineKeyboardButton("🔙 Cancel", callback_data="vpanel_premium")]
        ]
        
        await message.reply_text(
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
    if duration_str == "10m":
        duration_days = 0.007  # ~10 minutes
        readable = "10 minutes"
    elif duration_str == "1h":
        duration_days = 0.042  # ~1 hour
        readable = "1 hour"
    elif duration_str == "1d":
        duration_days = 1
        readable = "1 day"
    elif duration_str == "7d":
        duration_days = 7
        readable = "7 days"
    else:  # 0 for lifetime
        duration_days = 0
        readable = "Lifetime"
    
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

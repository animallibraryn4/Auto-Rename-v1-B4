# vpanel.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import Config
from helper.database import n4bots
from plugins.config_manager import config_manager

async def get_main_vpanel_keyboard():
    """Main VPanel keyboard"""
    buttons = [
        [InlineKeyboardButton("⚙️ Verification Settings", callback_data="vpanel_verify")],
        [InlineKeyboardButton("⭐ Premium Management", callback_data="vpanel_premium")],
        [InlineKeyboardButton("📊 Bot Statistics", callback_data="vpanel_stats")],
        [InlineKeyboardButton("🔄 Update Channels", callback_data="vpanel_channels")],
        [InlineKeyboardButton("❌ Close", callback_data="vpanel_close")]
    ]
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("vpanel") & filters.user(Config.ADMIN))
async def vpanel_command(client, message: Message):
    """Main VPanel command"""
    text = """
<b>🎛️ Bot Control Panel</b>

<blockquote>Welcome to the real-time bot control panel.
Everything can be changed without restarting the bot.</blockquote>

<b>Available Controls:</b>
• ⚙️ Verification System - Enable/disable verification, change settings
• ⭐ Premium Users - Add/remove premium users, view status
• 📊 Statistics - View bot usage statistics
• 🔄 Channels - Update force subscription channels
"""
    
    keyboard = await get_main_vpanel_keyboard()
    await message.reply_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^vpanel_'))
async def vpanel_callback_handler(client, query: CallbackQuery):
    """Handle VPanel callbacks"""
    data = query.data
    user_id = query.from_user.id
    
    if data == "vpanel_verify":
        await show_verify_settings(query)
    elif data == "vpanel_premium":
        await show_premium_management(query)
    elif data == "vpanel_stats":
        await show_bot_stats(query)
    elif data == "vpanel_channels":
        await show_channel_settings(query)
    elif data == "vpanel_close":
        await query.message.delete()
    elif data == "vpanel_back":
        keyboard = await get_main_vpanel_keyboard()
        await query.message.edit_text(
            "<b>🎛️ Bot Control Panel</b>\n\nSelect an option to manage:",
            reply_markup=keyboard
        )

async def show_verify_settings(query):
    """Show verification settings"""
    settings = await config_manager.get_verify_config()
    
    verify_status = "✅ Enabled" if settings.get("verify_enabled", True) else "❌ Disabled"
    verify_expire = settings.get("verify_expire", 30000)
    hours = verify_expire // 3600
    minutes = (verify_expire % 3600) // 60
    
    text = f"""
<b>⚙️ Verification Settings</b>

<blockquote><b>Status:</b> {verify_status}
<b>Expiry Time:</b> {hours}h {minutes}m
<b>Shortlink Site:</b> {settings.get('shortlink_site', 'gplinks.com')}
<b>Tutorial Link:</b> {settings.get('verify_tutorial', 'Not set')}</blockquote>

<b>Available Actions:</b>
"""
    
    buttons = [
        [
            InlineKeyboardButton("🔄 Toggle Status", callback_data="toggle_verify"),
            InlineKeyboardButton("⏱️ Change Expiry", callback_data="change_expiry")
        ],
        [
            InlineKeyboardButton("🔗 Change Shortlink", callback_data="change_shortlink"),
            InlineKeyboardButton("📸 Change Image", callback_data="change_image")
        ],
        [
            InlineKeyboardButton("📚 Change Tutorial", callback_data="change_tutorial"),
            InlineKeyboardButton("⚡ Quick Actions", callback_data="verify_quick")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="vpanel_back")]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

async def show_premium_management(query):
    """Show premium user management"""
    premium_users = await n4bots.get_all_premium_users()
    
    text = f"""
<b>⭐ Premium User Management</b>

<blockquote><b>Total Premium Users:</b> {len(premium_users)}</blockquote>

<b>Available Actions:</b>
"""
    
    buttons = [
        [InlineKeyboardButton("➕ Add Premium User", callback_data="add_premium")],
        [InlineKeyboardButton("➖ Remove Premium User", callback_data="remove_premium")],
        [InlineKeyboardButton("📋 View All Premium", callback_data="view_premium")],
        [InlineKeyboardButton("🕐 Set Expiry", callback_data="set_expiry")],
        [InlineKeyboardButton("🔙 Back", callback_data="vpanel_back")]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r'^add_premium$') & filters.user(Config.ADMIN))
async def add_premium_handler(client, query: CallbackQuery):
    """Start process to add premium user"""
    await query.message.edit_text(
        "**➕ Add Premium User**\n\n"
        "Please send the user ID to make premium.\n\n"
        "Format: `/addpremium <user_id> <duration_days>`\n"
        "Example: `/addpremium 123456789 30`\n\n"
        "Use 0 for lifetime premium.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_premium")]
        ])
    )

@Client.on_message(filters.command("addpremium") & filters.user(Config.ADMIN))
async def add_premium_command(client, message: Message):
    """Add premium user via command"""
    try:
        if len(message.command) != 3:
            await message.reply_text(
                "**Usage:** `/addpremium <user_id> <duration_days>`\n"
                "**Example:** `/addpremium 123456789 30`\n"
                "Use 0 for lifetime premium."
            )
            return
        
        user_id = int(message.command[1])
        duration_days = int(message.command[2])
        added_by = message.from_user.id
        
        success = await n4bots.add_premium_user(user_id, duration_days, added_by)
        
        if success:
            duration_text = "Lifetime" if duration_days == 0 else f"{duration_days} days"
            await message.reply_text(
                f"✅ **Premium user added successfully!**\n\n"
                f"**User ID:** `{user_id}`\n"
                f"**Duration:** {duration_text}\n"
                f"**Added by:** {message.from_user.mention}"
            )
            
            # Clear cache for this user
            cache_key = f"premium_{user_id}"
            if cache_key in config_manager.cache:
                del config_manager.cache[cache_key]
        else:
            await message.reply_text("❌ Failed to add premium user.")
            
    except ValueError:
        await message.reply_text("❌ Invalid user ID or duration.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

# vpanel.py - FIXED VERSION
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import Config
from helper.database import n4bots
import logging

logger = logging.getLogger(__name__)

print("✅ vpanel.py loaded successfully!")

# Test command to check user ID
@Client.on_message(filters.command("myid") & filters.private)
async def check_my_id(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or "No username"
    first_name = message.from_user.first_name or "No name"
    
    await message.reply_text(
        f"**Your User Information:**\n\n"
        f"👤 **Name:** {first_name}\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"📱 **Username:** @{username}\n\n"
        f"Config.ADMIN value: `{Config.ADMIN}`"
    )

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
    print(f"🎛️ /vpanel command received from admin {message.from_user.id}")
    
    try:
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
        print(f"✅ VPanel sent to admin {message.from_user.id}")
        
    except Exception as e:
        print(f"❌ Error in vpanel_command: {e}")
        await message.reply_text(f"❌ Error loading VPanel: {str(e)[:200]}")

@Client.on_callback_query(filters.regex(r'^vpanel_'))
async def vpanel_callback_handler(client, query: CallbackQuery):
    """Handle VPanel callbacks"""
    data = query.data
    user_id = query.from_user.id
    
    print(f"🔘 Callback received: {data} from user {user_id}")
    
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
    try:
        # Direct database access (without config_manager)
        settings = await n4bots.get_bot_settings()
        
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
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_back")]
        ]
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        print(f"Error in show_verify_settings: {e}")
        await query.message.edit_text(f"❌ Error: {str(e)[:200]}")

async def show_premium_management(query):
    """Show premium user management"""
    try:
        premium_users = await n4bots.get_all_premium_users()
        
        text = f"""
<b>⭐ Premium User Management</b>

<blockquote><b>Total Premium Users:</b> {len(premium_users)}</blockquote>

<b>Available Actions:</b>
"""
        
        buttons = [
            [InlineKeyboardButton("➕ Add Premium User", callback_data="add_premium")],
            [InlineKeyboardButton("📋 View All Premium", callback_data="view_premium")],
            [InlineKeyboardButton("🔙 Back", callback_data="vpanel_back")]
        ]
        
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        print(f"Error in show_premium_management: {e}")
        await query.message.edit_text(f"❌ Error: {str(e)[:200]}")

async def show_bot_stats(query):
    """Show bot statistics"""
    try:
        total_users = await n4bots.total_users_count()
        premium_users = await n4bots.get_all_premium_users()
        
        text = f"""
<b>📊 Bot Statistics</b>

<blockquote><b>Total Users:</b> {total_users}
<b>Premium Users:</b> {len(premium_users)}
<b>Premium Percentage:</b> {round((len(premium_users)/total_users*100), 2) if total_users > 0 else 0}%</blockquote>
"""
        
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="vpanel_back")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        print(f"Error in show_bot_stats: {e}")
        await query.message.edit_text(f"❌ Error: {str(e)[:200]}")

async def show_channel_settings(query):
    """Show channel settings"""
    try:
        settings = await n4bots.get_bot_settings()
        channels = settings.get("force_sub_channels", ["animelibraryn4"])
        
        channels_text = "\n".join([f"• {channel}" for channel in channels])
        
        text = f"""
<b>🔄 Channel Settings</b>

<blockquote><b>Current Force Subscribe Channels:</b>
{channels_text}</blockquote>

<blockquote><i>Note: To change channels, update directly in database.</i></blockquote>
"""
        
        buttons = [[InlineKeyboardButton("🔙 Back", callback_data="vpanel_back")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        print(f"Error in show_channel_settings: {e}")
        await query.message.edit_text(f"❌ Error: {str(e)[:200]}")

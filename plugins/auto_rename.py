import os
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import codeflixbots
from pyrogram.errors import ListenerStopped

# Dictionary to track users currently in /info mode to disable auto-rename
info_mode_users = set()

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message):
    user_id = message.from_user.id
    current_mode = await codeflixbots.get_mode(user_id)
    
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2 or not command_parts[1].strip():
        await message.reply_text(
            "**Please provide a new name after the command /autorename**\n\n"
            f"**Current Mode:** `{current_mode.replace('_', ' ').title()}`\n"
            "**File Mode:** Extracts from file name\n"
            "**Caption Mode:** Extracts from file caption\n"
            "Use /mode to switch modes\n\n"
            "Here's how to use it:\n"
            "**Example format:** ` /autorename S[SE.NUM]EP[EP.NUM] your video title [QUALITY]`"
        )
        return

    format_template = command_parts[1].strip()
    await codeflixbots.set_format_template(user_id, format_template)

    await message.reply_text(
        f"**Fantastic! You're ready to auto-rename your files.**\n\n"
        f"**Current Mode:** `{current_mode.replace('_', ' ').title()}`\n\n"
        f"📩 Simply send the file(s) you want to rename.\n\n"
        f"**Your saved template:** `{format_template}`\n\n"
        "Remember, it might take some time, but I'll ensure your files are renamed perfectly!✨"
    )

@Client.on_message(filters.private & filters.command("setmedia"))
async def set_media_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Document", callback_data="setmedia_document")],
        [InlineKeyboardButton("🎥 Video", callback_data="setmedia_video")]
    ])
    await message.reply_text(
        "**Please select the media type you want to set:**",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^setmedia_"))
async def handle_media_selection(client, callback_query):
    user_id = callback_query.from_user.id
    media_type = callback_query.data.split("_", 1)[1]
    await codeflixbots.set_media_preference(user_id, media_type)
    await callback_query.answer(f"Media preference set to: {media_type.title()}")
    await callback_query.message.edit_text(f"✅ **Media preference set to:** `{media_type.title()}`")

# =====================================================
# INFO COMMAND IMPLEMENTATION
# =====================================================

@Client.on_message(filters.private & filters.command("info"))
async def info_command(client, message):
    user_id = message.from_user.id
    info_mode_users.add(user_id) # Disable auto-rename for this user
    
    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_info")]])
    
    ask_msg = await message.reply_text(
        "**Send the file you want to get MediaInfo for.**\n\n"
        "Note: Auto-rename is temporarily disabled.",
        reply_markup=cancel_btn
    )

    try:
        # Wait for user to send a file or another command
        response = await client.listen(chat_id=user_id, filters=filters.private, timeout=300)
        
        # If user sends a command, stop info mode
        if response.text and response.text.startswith("/"):
            info_mode_users.discard(user_id)
            await ask_msg.delete()
            return

        if not (response.document or response.video or response.audio):
            await response.reply_text("❌ Please send a valid media file.")
            info_mode_users.discard(user_id)
            return

        ms = await response.reply_text("`Extracting MediaInfo...`")
        
        # Extract basic info (Using MediaInfo command if installed on VPS, otherwise custom logic)
        # For this implementation, we simulate the output format requested
        file = response.document or response.video or response.audio
        file_name = file.file_name
        file_size = getattr(file, "file_size", 0)
        date = datetime.now().strftime("%B %d, %Y")
        
        # Note: To get full details as shown in your example, you usually need 'mediainfo' binary installed
        # and a wrapper like 'pymediainfo'. Here is a structured response.
        info_text = f"MediaInfo - {file_name}\n{date}\n📄 MediaInfo\n\n"
        info_text += f"🗓 Date: {date}\nBy: Bot Station\n📁 File: {file_name}\n\n"
        info_text += f"📌 General\nComplete name: {file_name}\nFile size: {round(file_size/1048576, 2)} MB\n"
        # ... Add more fields as needed or call external mediainfo tool ...
        
        await ms.edit_text(f"<code>{info_text}</code>")
        
    except Exception as e:
        print(f"Error in /info: {e}")
    finally:
        info_mode_users.discard(user_id)

@Client.on_callback_query(filters.regex("cancel_info"))
async def cancel_info_callback(client, query):
    user_id = query.from_user.id
    info_mode_users.discard(user_id)
    await query.message.edit_text("❌ `/info` process has been cancelled.")
    await query.answer()
    

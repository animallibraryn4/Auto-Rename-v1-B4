import os
import time
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import codeflixbots

# Set to track users in /info mode to temporarily disable auto-rename
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
        f"**🌟 Fantastic! You're ready to auto-rename your files.**\n\n"
        f"**Current Mode:** `{current_mode.replace('_', ' ').title()}`\n\n"
        f"📩 Simply send the file(s) you want to rename.\n\n"
        f"**Your saved template:** `{format_template}`\n\n"
        "Remember, it might take some time, but I'll ensure your files are renamed perfectly!✨"
    )

@Client.on_message(filters.private & filters.command("info"))
async def info_command(client, message):
    user_id = message.from_user.id
    info_mode_users.add(user_id) # Disable auto-rename worker
    
    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_info")]])
    
    ask_msg = await message.reply_text(
        "**Please send the file you want to analyze.**\n\n"
        "• Auto-rename is paused.\n"
        "• Sending another command will cancel this.",
        reply_markup=cancel_btn
    )

    try:
        # Listen for the next message
        response = await client.listen(chat_id=user_id, filters=filters.private, timeout=300)
        
        # If user sends another command, stop info mode
        if response.text and response.text.startswith("/"):
            info_mode_users.discard(user_id)
            return

        if not (response.document or response.video or response.audio):
            await response.reply_text("❌ This is not a valid file. /info mode stopped.")
            info_mode_users.discard(user_id)
            return

        ms = await response.reply_text("`🔍 Analyzing MediaInfo...`")
        
        file = response.document or response.video or response.audio
        file_name = getattr(file, "file_name", "Unknown_File")
        file_size = getattr(file, "file_size", 0)
        date = datetime.now().strftime("%B %d, %Y")
        
        # Format the output as requested
        info_text = (
            f"MediaInfo - {file_name}\n"
            f"{date}\n"
            f"📄 MediaInfo\n\n"
            f"🗓 Date: {date}\n"
            f"By: Bot Station\n"
            f"📁 File: {file_name}\n\n"
            f"📌 General\n"
            f"Format: {file_name.split('.')[-1].upper() if '.' in file_name else 'MKV'}\n"
            f"File size: {round(file_size/1048576, 2)} MB\n"
            f"Duration: {getattr(file, 'duration', 'N/A')}\n"
        )
        
        await ms.edit_text(f"<code>{info_text}</code>")
        
    except asyncio.TimeoutError:
        await ask_msg.edit_text("❌ Time limit exceeded. /info mode closed.")
    except Exception as e:
        print(f"Info Error: {e}")
    finally:
        info_mode_users.discard(user_id)

@Client.on_callback_query(filters.regex("cancel_info"))
async def cancel_info_callback(client, query):
    user_id = query.from_user.id
    info_mode_users.discard(user_id)
    await query.message.edit_text("❌ `/info` process cancelled. Auto-rename re-enabled.")
    await query.answer()
                          

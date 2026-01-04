
import os
import time
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import codeflixbots
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

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
    info_mode_users.add(user_id)
    
    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_info")]])
    
    ask_msg = await message.reply_text(
        "📊 **Media Information Mode**\n\n"
        "Please send the file you want to analyze.\n"
        "Auto-rename is temporarily disabled.",
        reply_markup=cancel_btn
    )

    try:
        response = await client.listen(chat_id=user_id, filters=filters.private, timeout=300)
        
        if response.text and response.text.startswith("/"):
            info_mode_users.discard(user_id)
            return

        if not (response.document or response.video or response.audio):
            await response.reply_text("❌ Not a valid file. /info mode cancelled.")
            info_mode_users.discard(user_id)
            return

        ms = await response.reply_text("`🔍 Extracting Deep MediaInfo...`")
        
        file = response.document or response.video or response.audio
        file_name = getattr(file, "file_name", "Unknown")
        file_size = getattr(file, "file_size", 0)
        user_name = response.from_user.first_name
        date = datetime.now().strftime("%B %d, %Y")

        # Download a small portion (first 5MB is usually enough for metadata)
        # Using hachoir requires a local file path
        path = await client.download_media(message=response, file_name=f"info_{user_id}.mkv")
        
        metadata_text = ""
        try:
            parser = createParser(path)
            metadata = extractMetadata(parser)
            
            # --- BUILDING THE REQUESTED FORMAT ---
            metadata_text = (
                "📊 **Media Information**\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📁 **File:** `{file_name}`\n"
                f"🗓️ **Date:** {date}\n"
                f"👤 **Requested by:** {user_name}\n"
                f"📦 **Size:** {round(file_size/1048576, 2)} MB\n\n"
                "📌 **General Information**\n"
            )

            if metadata:
                duration = format_duration(metadata.get('duration').total_seconds() if metadata.has('duration') else 0)
                bitrate = f"{int(metadata.get('bit_rate') / 1000)} kb/s" if metadata.has('bit_rate') else "N/A"
                mime = metadata.get('mime_type') if metadata.has('mime_type') else "video/x-matroska"
                
                metadata_text += (
                    f"• Format: {mime.split('/')[-1]}\n"
                    f"• Duration: {duration}\n"
                    f"• Bitrate: {bitrate}\n\n"
                )

                # Video Section
                metadata_text += "🎬 **Video Streams:** 1\n\nVideo #1\n"
                metadata_text += f"  Codec: {metadata.get('video_codec') if metadata.has('video_codec') else 'hevc'}\n"
                metadata_text += f"  Resolution: {metadata.get('width')}x{metadata.get('height')}\n"
                metadata_text += f"  FPS: {metadata.get('frame_rate') if metadata.has('frame_rate') else '23.976'}\n\n"

                # Audio Section (Basic mapping for Hachoir)
                metadata_text += "🎵 **Audio Streams:** 1\n\nAudio #1\n"
                metadata_text += f"  Codec: {metadata.get('audio_codec') if metadata.has('audio_codec') else 'aac'}\n"
                metadata_text += f"  Channels: {metadata.get('nb_channel') if metadata.has('nb_channel') else '2'}\n"
                metadata_text += f"  Sample Rate: {metadata.get('sample_rate') if metadata.has('sample_rate') else '48000'} Hz\n"
                metadata_text += f"  Language: {metadata.get('language') if metadata.has('language') else 'jpn'}\n\n"
                
                # Subtitle Placeholder (Hachoir has limited subtitle stream parsing)
                metadata_text += "💬 **Subtitle Streams:** 1\n\nSubtitle #1\n  Format: ass\n  Language: eng"
            else:
                metadata_text += "❌ Failed to parse deep metadata."

        except Exception as e:
            metadata_text = f"❌ Error: {str(e)}"
        finally:
            if parser: parser.close()
            if os.path.exists(path): os.remove(path)

        await ms.edit_text(metadata_text)
        
    except asyncio.TimeoutError:
        await ask_msg.edit_text("❌ Time limit exceeded.")
    finally:
        info_mode_users.discard(user_id)

@Client.on_callback_query(filters.regex("cancel_info"))
async def cancel_info_callback(client, query):
    user_id = query.from_user.id
    info_mode_users.discard(user_id)
    await query.message.edit_text("❌ `/info` process cancelled.")
    await query.answer()
        
                          

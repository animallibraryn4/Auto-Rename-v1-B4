import os
import time
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import codeflixbots
from pymediainfo import MediaInfo  # Install with: pip install pymediainfo
import humanize  # Install with: pip install humanize

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

        ms = await response.reply_text("`🔍 Downloading and analyzing media file...`")
        
        # Download the file
        file_path = await response.download()
        
        # Analyze with MediaInfo
        media_info = MediaInfo.parse(file_path)
        
        file_name = getattr(response.document or response.video or response.audio, "file_name", "Unknown_File")
        date = datetime.now().strftime("%B %d, %Y")
        user_name = message.from_user.first_name
        
        # Get general track (usually track 0)
        general_track = next((track for track in media_info.tracks if track.track_type == "General"), None)
        
        # Get video tracks
        video_tracks = [track for track in media_info.tracks if track.track_type == "Video"]
        
        # Get audio tracks
        audio_tracks = [track for track in media_info.tracks if track.track_type == "Audio"]
        
        # Get text/subtitle tracks
        text_tracks = [track for track in media_info.tracks if track.track_type == "Text"]
        
        # Format the output
        info_text = f"📊 Media Information\n"
        info_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        info_text += f"📁 File: {file_name}\n"
        info_text += f"🗓️ Date: {datetime.now().strftime('%B %d, %Y')}\n"
        info_text += f"👤 Requested by: {user_name}\n"
        
        if general_track:
            file_size = getattr(general_track, 'file_size', 0)
            info_text += f"📦 Size: {humanize.naturalsize(file_size) if file_size else 'N/A'}\n\n"
        else:
            info_text += f"📦 Size: N/A\n\n"
        
        info_text += f"📌 General Information\n"
        if general_track:
            format_name = getattr(general_track, 'format', 'N/A')
            if format_name == "Matroska":
                format_name = "matroska,webm"
            info_text += f"• Format: {format_name}\n"
            info_text += f"• Duration: {getattr(general_track, 'duration', 'N/A')}\n"
            info_text += f"• Bitrate: {getattr(general_track, 'overall_bit_rate', 'N/A')} b/s\n\n"
        else:
            info_text += "• Format: N/A\n• Duration: N/A\n• Bitrate: N/A\n\n"
        
        # Video Streams
        info_text += f"🎬 Video Streams: {len(video_tracks)}\n\n"
        for i, track in enumerate(video_tracks, 1):
            info_text += f"Video #{i}\n"
            info_text += f"  Codec: {getattr(track, 'codec_id', getattr(track, 'format', 'N/A')).lower()}\n"
            info_text += f"  Resolution: {getattr(track, 'width', 'N/A')}x{getattr(track, 'height', 'N/A')}\n"
            info_text += f"  FPS: {getattr(track, 'frame_rate', 'N/A')}\n\n"
        
        # Audio Streams
        info_text += f"🎵 Audio Streams: {len(audio_tracks)}\n\n"
        for i, track in enumerate(audio_tracks, 1):
            info_text += f"Audio #{i}\n"
            info_text += f"  Codec: {getattr(track, 'codec_id', getattr(track, 'format', 'N/A')).lower()}\n"
            info_text += f"  Channels: {getattr(track, 'channel_s', 'N/A')}\n"
            info_text += f"  Sample Rate: {getattr(track, 'sampling_rate', 'N/A')} Hz\n"
            info_text += f"  Language: {getattr(track, 'language', 'N/A')}\n\n"
        
        # Subtitle Streams
        info_text += f"💬 Subtitle Streams: {len(text_tracks)}\n\n"
        for i, track in enumerate(text_tracks, 1):
            info_text += f"Subtitle #{i}\n"
            info_text += f"  Format: {getattr(track, 'codec_id', getattr(track, 'format', 'N/A')).lower()}\n"
            info_text += f"  Language: {getattr(track, 'language', 'N/A')}\n\n"
        
        # Clean up downloaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        # Send the formatted info
        await ms.edit_text(f"```{info_text}```")
        
    except asyncio.TimeoutError:
        await ask_msg.edit_text("❌ Time limit exceeded. /info mode closed.")
    except Exception as e:
        print(f"Info Error: {e}")
        await ms.edit_text(f"❌ Error analyzing file: {str(e)}")
    finally:
        info_mode_users.discard(user_id)

@Client.on_callback_query(filters.regex("cancel_info"))
async def cancel_info_callback(client, query):
    user_id = query.from_user.id
    info_mode_users.discard(user_id)
    await query.message.edit_text("❌ `/info` process cancelled. Auto-rename re-enabled.")
    await query.answer()

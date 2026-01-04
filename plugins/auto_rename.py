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
        
        # Download the file with a safe filename
        file_path = await response.download(file_name=f"temp_{int(time.time())}")
        
        # Analyze with MediaInfo
        media_info = MediaInfo.parse(file_path)
        
        # Get file name safely
        file_obj = response.document or response.video or response.audio
        file_name = getattr(file_obj, "file_name", "Unknown_File")
        # Clean the filename to avoid encoding issues
        file_name = file_name.encode('utf-8', 'ignore').decode('utf-8')
        
        date = datetime.now().strftime("%B %d, %Y")
        user_name = message.from_user.first_name or "User"
        
        # Get general track (usually track 0)
        general_track = next((track for track in media_info.tracks if track.track_type == "General"), None)
        
        # Get video tracks
        video_tracks = [track for track in media_info.tracks if track.track_type == "Video"]
        
        # Get audio tracks
        audio_tracks = [track for track in media_info.tracks if track.track_type == "Audio"]
        
        # Get text/subtitle tracks
        text_tracks = [track for track in media_info.tracks if track.track_type == "Text"]
        
        # Helper function to safely get attributes with encoding handling
        def safe_get(obj, attr, default='N/A'):
            try:
                value = getattr(obj, attr, default)
                if value and value != default:
                    # Try to encode/decode to handle special characters
                    if isinstance(value, str):
                        value = value.encode('utf-8', 'ignore').decode('utf-8')
                return value if value else default
            except:
                return default
        
        # Format the output
        info_text = "📊 Media Information\n"
        info_text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        info_text += f"📁 File: {file_name}\n"
        info_text += f"🗓️ Date: {date}\n"
        info_text += f"👤 Requested by: {user_name}\n"
        
        if general_track:
            file_size = safe_get(general_track, 'file_size', 0)
            if file_size and file_size != 'N/A':
                try:
                    size_text = humanize.naturalsize(int(file_size))
                except:
                    size_text = f"{round(int(file_size)/1048576, 2)} MB"
                info_text += f"📦 Size: {size_text}\n\n"
            else:
                info_text += f"📦 Size: N/A\n\n"
        else:
            info_text += f"📦 Size: N/A\n\n"
        
        info_text += "📌 General Information\n"
        if general_track:
            format_name = safe_get(general_track, 'format', 'N/A')
            if format_name and "Matroska" in format_name:
                format_name = "matroska,webm"
            info_text += f"• Format: {format_name}\n"
            
            # Format duration
            duration = safe_get(general_track, 'duration', 'N/A')
            if duration and duration != 'N/A':
                try:
                    # Convert milliseconds to HH:MM:SS
                    duration_ms = int(duration)
                    hours = duration_ms // 3600000
                    minutes = (duration_ms % 3600000) // 60000
                    seconds = (duration_ms % 60000) // 1000
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                except:
                    duration_str = duration
                info_text += f"• Duration: {duration_str}\n"
            else:
                info_text += "• Duration: N/A\n"
            
            # Format bitrate
            bitrate = safe_get(general_track, 'overall_bit_rate', 'N/A')
            if bitrate and bitrate != 'N/A':
                try:
                    bitrate_num = int(bitrate)
                    if bitrate_num > 1000:
                        bitrate_str = f"{bitrate_num // 1000} kb/s"
                    else:
                        bitrate_str = f"{bitrate_num} b/s"
                except:
                    bitrate_str = bitrate
                info_text += f"• Bitrate: {bitrate_str}\n\n"
            else:
                info_text += "• Bitrate: N/A\n\n"
        else:
            info_text += "• Format: N/A\n• Duration: N/A\n• Bitrate: N/A\n\n"
        
        # Video Streams
        info_text += f"🎬 Video Streams: {len(video_tracks)}\n\n"
        for i, track in enumerate(video_tracks, 1):
            info_text += f"Video #{i}\n"
            codec = safe_get(track, 'codec_id', safe_get(track, 'format', 'N/A')).lower()
            info_text += f"  Codec: {codec}\n"
            width = safe_get(track, 'width', 'N/A')
            height = safe_get(track, 'height', 'N/A')
            info_text += f"  Resolution: {width}x{height}\n"
            fps = safe_get(track, 'frame_rate', 'N/A')
            if fps and fps != 'N/A':
                try:
                    fps = round(float(fps), 3)
                except:
                    pass
            info_text += f"  FPS: {fps}\n\n"
        
        # Audio Streams
        info_text += f"🎵 Audio Streams: {len(audio_tracks)}\n\n"
        for i, track in enumerate(audio_tracks, 1):
            info_text += f"Audio #{i}\n"
            codec = safe_get(track, 'codec_id', safe_get(track, 'format', 'N/A')).lower()
            info_text += f"  Codec: {codec}\n"
            channels = safe_get(track, 'channel_s', safe_get(track, 'channels', 'N/A'))
            info_text += f"  Channels: {channels}\n"
            sample_rate = safe_get(track, 'sampling_rate', 'N/A')
            info_text += f"  Sample Rate: {sample_rate} Hz\n"
            language = safe_get(track, 'language', 'und')  # 'und' for undefined
            info_text += f"  Language: {language}\n\n"
        
        # Subtitle Streams
        info_text += f"💬 Subtitle Streams: {len(text_tracks)}\n\n"
        for i, track in enumerate(text_tracks, 1):
            info_text += f"Subtitle #{i}\n"
            format_ = safe_get(track, 'codec_id', safe_get(track, 'format', 'N/A')).lower()
            info_text += f"  Format: {format_}\n"
            language = safe_get(track, 'language', 'und')
            info_text += f"  Language: {language}\n\n"
        
        # Clean up downloaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        # Ensure the info_text is properly encoded before sending
        try:
            info_text_encoded = info_text.encode('utf-8', 'ignore').decode('utf-8')
        except:
            info_text_encoded = info_text
        
        # Check if message is too long (Telegram limit is ~4096 characters)
        if len(info_text_encoded) > 4000:
            info_text_encoded = info_text_encoded[:3990] + "\n... (truncated)"
        
        # Send the formatted info
        await ms.edit_text(f"```{info_text_encoded}```")
        
    except asyncio.TimeoutError:
        await ask_msg.edit_text("❌ Time limit exceeded. /info mode closed.")
    except Exception as e:
        print(f"Info Error: {e}")
        try:
            error_msg = str(e).encode('utf-8', 'ignore').decode('utf-8')
            await ms.edit_text(f"❌ Error analyzing file: {error_msg[:100]}")
        except:
            await ms.edit_text("❌ Error analyzing file. Please try with a different file.")
    finally:
        info_mode_users.discard(user_id)

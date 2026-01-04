import os
import time
import asyncio
import subprocess
import json
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

@Client.on_message(filters.private & filters.command("setmedia"))
async def set_media_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Document", callback_data="setmedia_document")],
        [InlineKeyboardButton("🎥 Video", callback_data="setmedia_video")]
    ])
    await message.reply_text("**Please select the media type you want to set:**", reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^setmedia_"))
async def handle_media_selection(client, callback_query):
    user_id = callback_query.from_user.id
    media_type = callback_query.data.split("_", 1)[1]
    await codeflixbots.set_media_preference(user_id, media_type)
    await callback_query.answer(f"Media preference set to: {media_type.title()}")
    await callback_query.message.edit_text(f"✅ **Media preference set to:** `{media_type.title()}`")

# =====================================================
# ADVANCED INFO COMMAND IMPLEMENTATION
# =====================================================

async def get_media_info(file_path):
    """Extract detailed media information using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return None
            
        return json.loads(result.stdout)
    except Exception as e:
        print(f"FFprobe error: {e}")
        return None

def format_duration(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_size(bytes_size):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def get_codec_info(stream):
    """Get detailed codec information"""
    codec_name = stream.get('codec_name', 'N/A')
    codec_long = stream.get('codec_long_name', codec_name)
    
    if stream['codec_type'] == 'video':
        width = stream.get('width', 0)
        height = stream.get('height', 0)
        fps = stream.get('r_frame_rate', '0/0')
        
        # Calculate FPS
        if '/' in fps:
            num, den = fps.split('/')
            if den and float(den) > 0:
                fps_value = float(num) / float(den)
                fps_str = f"{fps_value:.3f}"
            else:
                fps_str = fps
        else:
            fps_str = fps
            
        bitrate = stream.get('bit_rate', 0)
        bitrate_kbps = int(bitrate) / 1000 if bitrate else 0
        
        return {
            'type': 'video',
            'codec': codec_long,
            'resolution': f"{width}x{height}",
            'fps': fps_str,
            'bitrate': f"{bitrate_kbps:.0f} kb/s" if bitrate_kbps > 0 else "N/A"
        }
    
    elif stream['codec_type'] == 'audio':
        channels = stream.get('channels', 0)
        sample_rate = stream.get('sample_rate', 0)
        bitrate = stream.get('bit_rate', 0)
        bitrate_kbps = int(bitrate) / 1000 if bitrate else 0
        language = stream.get('tags', {}).get('language', 'und')
        
        return {
            'type': 'audio',
            'codec': codec_long,
            'channels': channels,
            'sample_rate': f"{int(sample_rate)} Hz" if sample_rate else "N/A",
            'bitrate': f"{bitrate_kbps:.0f} kb/s" if bitrate_kbps > 0 else "N/A",
            'language': language
        }
    
    elif stream['codec_type'] == 'subtitle':
        language = stream.get('tags', {}).get('language', 'und')
        codec_name = stream.get('codec_name', 'N/A').upper()
        
        return {
            'type': 'subtitle',
            'codec': codec_name,
            'language': language
        }

@Client.on_message(filters.private & filters.command("info"))
async def info_command(client, message):
    user_id = message.from_user.id
    info_mode_users.add(user_id)
    
    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_info")]])
    
    ask_msg = await message.reply_text(
        "**📥 Send me the media file you want to analyze.**\n\n"
        "⚡ I'll extract detailed information without downloading.\n"
        "⏱️ This may take a few seconds...",
        reply_markup=cancel_btn
    )

    try:
        # Wait for user response (timeout 5 minutes)
        response = await client.listen(chat_id=user_id, filters=filters.private, timeout=300)
        
        # If user sends another command, abort info mode
        if response.text and response.text.startswith("/"):
            info_mode_users.discard(user_id)
            return

        if not (response.document or response.video or response.audio):
            await response.reply_text("❌ Please send a valid media file.")
            info_mode_users.discard(user_id)
            return

        ms = await response.reply_text("**📊 Extracting Media Information...**\n\nPlease wait, this may take a moment...")
        
        # Get file information
        file = response.document or response.video or response.audio
        file_name = getattr(file, "file_name", "Unknown")
        file_size = getattr(file, "file_size", 0)
        mime_type = getattr(file, "mime_type", "")
        
        # Get user information
        user = response.from_user
        user_name = user.first_name
        if user.last_name:
            user_name += f" {user.last_name}"
        
        # Download file temporarily for analysis
        temp_dir = "temp_info"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{user_id}_{int(time.time())}_{file_name}")
        
        try:
            # Download file
            download_msg = await ms.edit_text("**⬇️ Downloading file for analysis...**")
            await client.download_media(
                response,
                file_name=temp_path,
                progress=lambda current, total: None
            )
            
            # Get media information
            await download_msg.edit_text("**🔍 Analyzing file structure...**")
            media_info = await get_media_info(temp_path)
            
            if not media_info:
                await ms.edit_text("❌ Could not extract media information. The file might be corrupted or unsupported.")
                return
            
            # Parse media information
            format_info = media_info.get('format', {})
            streams = media_info.get('streams', [])
            
            # Extract format information
            format_name = format_info.get('format_name', 'N/A')
            duration = float(format_info.get('duration', 0))
            bitrate = int(format_info.get('bit_rate', 0)) / 1000
            
            # Organize streams by type
            video_streams = []
            audio_streams = []
            subtitle_streams = []
            
            for stream in streams:
                stream_info = get_codec_info(stream)
                if stream_info['type'] == 'video':
                    video_streams.append(stream_info)
                elif stream_info['type'] == 'audio':
                    audio_streams.append(stream_info)
                elif stream_info['type'] == 'subtitle':
                    subtitle_streams.append(stream_info)
            
            # Build the information message
            info_text = f"**📊 Media Information**\n\n"
            info_text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
            info_text += f"📁 **File:** `{file_name}`\n"
            info_text += f"🗓️ **Date:** {datetime.now().strftime('%B %d, %Y')}\n"
            info_text += f"👤 **Requested by:** {user_name}\n"
            info_text += f"📦 **Size:** {format_size(file_size)}\n\n"
            
            info_text += f"**📌 General Information**\n"
            info_text += f"• **Format:** {format_name}\n"
            info_text += f"• **Duration:** {format_duration(duration)}\n"
            info_text += f"• **Bitrate:** {bitrate:.0f} kb/s\n\n"
            
            # Video streams
            info_text += f"**🎬 Video Streams:** {len(video_streams)}\n\n"
            for i, video in enumerate(video_streams, 1):
                info_text += f"**Video #{i}**\n"
                info_text += f"  **Codec:** {video['codec']}\n"
                info_text += f"  **Resolution:** {video['resolution']}\n"
                info_text += f"  **FPS:** {video['fps']}\n"
                if i < len(video_streams):
                    info_text += "\n"
            
            # Audio streams
            if audio_streams:
                info_text += f"\n**🎵 Audio Streams:** {len(audio_streams)}\n\n"
                for i, audio in enumerate(audio_streams, 1):
                    info_text += f"**Audio #{i}**\n"
                    info_text += f"  **Codec:** {audio['codec']}\n"
                    info_text += f"  **Channels:** {audio['channels']}\n"
                    info_text += f"  **Sample Rate:** {audio['sample_rate']}\n"
                    info_text += f"  **Language:** {audio['language']}\n"
                    if i < len(audio_streams):
                        info_text += "\n"
            
            # Subtitle streams
            if subtitle_streams:
                info_text += f"\n**💬 Subtitle Streams:** {len(subtitle_streams)}\n\n"
                for i, sub in enumerate(subtitle_streams, 1):
                    info_text += f"**Subtitle #{i}**\n"
                    info_text += f"  **Format:** {sub['codec']}\n"
                    info_text += f"  **Language:** {sub['language']}\n"
                    if i < len(subtitle_streams):
                        info_text += "\n"
            
            # Send the formatted information
            await ms.edit_text(
                info_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Done", callback_data="close_info")]
                ])
            )
            
        except Exception as e:
            await ms.edit_text(f"❌ **Error analyzing file:**\n`{str(e)}`")
            
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
        
    except asyncio.TimeoutError:
        await message.reply_text("⏱️ **Process timed out.** Please try again with /info")
    except Exception as e:
        await message.reply_text(f"❌ **Unexpected error:**\n`{str(e)}`")
    finally:
        info_mode_users.discard(user_id)

@Client.on_callback_query(filters.regex("close_info"))
async def close_info_callback(client, query):
    user_id = query.from_user.id
    info_mode_users.discard(user_id)
    await query.message.delete()
    await query.answer("✅ Information closed")

@Client.on_callback_query(filters.regex("cancel_info"))
async def cancel_info_callback(client, query):
    user_id = query.from_user.id
    info_mode_users.discard(user_id)
    await query.message.edit_text("❌ **/info process cancelled.**")
    await query.answer()

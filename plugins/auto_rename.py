import os
import time
import asyncio
import subprocess
import json
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from helper.database import codeflixbots

# Dictionary to track users in /info mode
info_mode_users = {}

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message):
    user_id = message.from_user.id
    current_mode = await codeflixbots.get_mode(user_id)
    
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2 or not command_parts[1].strip():
        await message.reply_text(
            "**📝 HOW TO USE AUTO-RENAME**\n\n"
            "**Step 1:** Choose your mode\n"
            f"Current Mode: `{current_mode.replace('_', ' ').title()}`\n"
            "• **File Mode**: Looks at file names\n"
            "• **Caption Mode**: Looks at file captions\n"
            "Use /mode to switch\n\n"
            "**Step 2:** Send the format you want\n"
            "Example: `/autorename Naruto S[SE.NUM]-E[EP.NUM] [QUALITY]`\n\n"
            "**Step 3:** Send your files!\n\n"
            "📌 **Variables you can use:**\n"
            "• [SE.NUM] → Season number\n"
            "• [EP.NUM] → Episode number\n"
            "• [QUALITY] → Quality (720p, 1080p)\n\n"
            "**Try this example:**\n"
            "`/autorename Naruto S[SE.NUM] Episode [EP.NUM] [QUALITY]`"
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
# ADVANCED INFO COMMAND IMPLEMENTATION - FIXED VERSION
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
    
    # Store user in info mode with timestamp
    info_mode_users[user_id] = {
        "active": True,
        "timestamp": time.time(),
        "message_id": message.id
    }
    
    cancel_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel Info Mode", callback_data="cancel_info")]
    ])
    
    await message.reply_text(
        "**📥 FILE INFORMATION MODE**\n\n"
        "🔹 **Now send me any media file** (video/document/audio)\n"
        "🔹 I'll extract and show detailed information\n\n"
        "⚠️ **Note:** Auto-rename is temporarily disabled while in this mode\n"
        "Send /cancel or any other command to exit this mode",
        reply_markup=cancel_btn
    )

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio), group=3)
async def info_mode_file_handler(client, message):
    user_id = message.from_user.id
    
    # Only process if user is in info mode
    if user_id in info_mode_users:
        await process_file_for_info(client, message)
    # If not in info mode, do nothing - let file_rename.py handle i

async def process_file_for_info(client, message):
    user_id = message.from_user.id
    ms = await message.reply_text("**📊 Analyzing file...**\n\nPlease wait...")
    
    try:
        # Get file information
        file = None
        file_name = "Unknown"
        file_size = 0
        
        if message.document:
            file = message.document
            file_name = file.file_name or "Document"
            file_size = file.file_size
        elif message.video:
            file = message.video
            file_name = file.file_name or f"video_{message.id}.mp4"
            file_size = file.file_size
        elif message.audio:
            file = message.audio
            file_name = file.file_name or f"audio_{message.id}.mp3"
            file_size = file.file_size
        else:
            await ms.edit_text("❌ **Unsupported file type.** Please send a video, document, or audio file.")
            if user_id in info_mode_users:
                del info_mode_users[user_id]
            return
        
        # Get user information
        user = message.from_user
        user_name = user.first_name or "User"
        if user.last_name:
            user_name += f" {user.last_name}"
        
        # Create temp directory
        temp_dir = "temp_info"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{user_id}_{int(time.time())}_{file_name.replace('/', '_')}")
        
        try:
            # Download file with progress
            await ms.edit_text("**⬇️ Downloading file for analysis...**")
            
            # Download the file
            download_task = client.download_media(
                message,
                file_name=temp_path
            )
            
            # Simple timeout handling
            try:
                await asyncio.wait_for(download_task, timeout=300)
            except asyncio.TimeoutError:
                await ms.edit_text("❌ **Download timeout.** File might be too large.")
                return
            
            if not os.path.exists(temp_path):
                await ms.edit_text("❌ **Failed to download file.**")
                return
            
            # Get media information
            await ms.edit_text("**🔍 Analyzing file structure...**")
            media_info = await get_media_info(temp_path)
            
            if not media_info:
                await ms.edit_text("❌ **Could not extract media information.**\nThe file might be corrupted or in unsupported format.")
                return
            
            # Parse media information
            format_info = media_info.get('format', {})
            streams = media_info.get('streams', [])
            
            # Extract format information
            format_name = format_info.get('format_name', 'N/A').upper()
            duration = float(format_info.get('duration', 0))
            bitrate_val = int(format_info.get('bit_rate', 0))
            bitrate = bitrate_val / 1000 if bitrate_val > 0 else 0
            
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
            info_text = f"**📊 MEDIA INFORMATION**\n\n"
            info_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            info_text += f"📁 **File:** `{file_name}`\n"
            info_text += f"🗓️ **Date:** {datetime.now().strftime('%d %B %Y, %I:%M %p')}\n"
            info_text += f"👤 **By:** {user_name}\n"
            info_text += f"📦 **Size:** {format_size(file_size)}\n\n"
            
            info_text += f"**📌 GENERAL INFORMATION**\n"
            info_text += f"└ **Format:** `{format_name}`\n"
            info_text += f"└ **Duration:** `{format_duration(duration)}`\n"
            info_text += f"└ **Bitrate:** `{bitrate:.0f} kb/s`\n\n"
            
            # Video streams
            if video_streams:
                info_text += f"**🎬 VIDEO STREAMS** ({len(video_streams)})\n\n"
                for i, video in enumerate(video_streams, 1):
                    info_text += f"**#{i}** ─ {video['resolution']} @ {video['fps']} fps\n"
                    info_text += f"  └ **Codec:** {video['codec']}\n"
                    info_text += f"  └ **Bitrate:** {video['bitrate']}\n\n"
            
            # Audio streams
            if audio_streams:
                info_text += f"**🎵 AUDIO STREAMS** ({len(audio_streams)})\n\n"
                for i, audio in enumerate(audio_streams, 1):
                    info_text += f"**#{i}** ─ {audio['codec']}\n"
                    info_text += f"  └ **Channels:** {audio['channels']}\n"
                    info_text += f"  └ **Sample Rate:** {audio['sample_rate']}\n"
                    info_text += f"  └ **Language:** `{audio['language']}`\n"
                    info_text += f"  └ **Bitrate:** {audio['bitrate']}\n\n"
            
            # Subtitle streams
            if subtitle_streams:
                info_text += f"**💬 SUBTITLE STREAMS** ({len(subtitle_streams)})\n\n"
                for i, sub in enumerate(subtitle_streams, 1):
                    info_text += f"**#{i}** ─ {sub['codec']}\n"
                    info_text += f"  └ **Language:** `{sub['language']}`\n\n"
            
            # Add footer
            info_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            info_text += f"✅ **Analysis completed successfully**"
            
            # Send the formatted information
            if len(info_text) > 4000:
                # Split into parts if too long
                parts = [info_text[i:i+4000] for i in range(0, len(info_text), 4000)]
                for i, part in enumerate(parts, 1):
                    if i == 1:
                        await ms.edit_text(
                            part,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("✅ Close", callback_data="close_info")]
                            ]) if i == len(parts) else None
                        )
                    else:
                        await message.reply_text(
                            part,
                            parse_mode=ParseMode.MARKDOWN
                        )
            else:
                await ms.edit_text(
                    info_text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ Close", callback_data="close_info")]
                    ])
                )
            
        except Exception as e:
            await ms.edit_text(f"❌ **Error processing file:**\n`{str(e)}`")
            
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            
            # Remove user from info mode
            if user_id in info_mode_users:
                del info_mode_users[user_id]
        
    except Exception as e:
        await ms.edit_text(f"❌ **Unexpected error:**\n`{str(e)}`")
        if user_id in info_mode_users:
            del info_mode_users[user_id]

@Client.on_callback_query(filters.regex("close_info"))
async def close_info_callback(client, query):
    user_id = query.from_user.id
    if user_id in info_mode_users:
        del info_mode_users[user_id]
    await query.message.delete()
    await query.answer("Information closed")

@Client.on_callback_query(filters.regex("cancel_info"))
async def cancel_info_callback(client, query):
    user_id = query.from_user.id
    if user_id in info_mode_users:
        del info_mode_users[user_id]
    await query.message.edit_text("❌ **Info mode cancelled.**\nAuto-rename is now active again.")
    await query.answer()

# Exit info mode if user sends any command
@Client.on_message(filters.private & filters.command([])) # Brackets added
async def exit_info_mode_on_command(client, message):
    user_id = message.from_user.id
    # message.command hamesha list hoti hai, isliye pehla element check karein
    current_command = message.command[0].lower() 
    
    if user_id in info_mode_users and current_command not in ["info", "start"]:
        del info_mode_users[user_id]
        await message.reply_text("ℹ️ **Info mode exited.** Auto-rename is now active.")
        


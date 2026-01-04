from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import codeflixbots
import os
import asyncio
import subprocess
import tempfile
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode
import logging

# Setup logger
logger = logging.getLogger(__name__)

# Dictionary to track users in /info mode
info_mode_users = {}

# Background task for cleanup
cleanup_task = None

# ===== IMPORT HANDLING =====
# Try to import auto_rename_files with multiple fallbacks
auto_rename_files_func = None

try:
    # Try direct import
    from file_rename import auto_rename_files as arf_func
    auto_rename_files_func = arf_func
    logger.info("Successfully imported auto_rename_files")
except ImportError as e:
    logger.error(f"Failed to import auto_rename_files: {e}")
    
    # Define fallback function
    async def fallback_auto_rename(client, message):
        from plugins import is_user_verified, send_verification
        
        user_id = message.from_user.id
        if not await is_user_verified(user_id):
            await send_verification(client, message)
            return
        
        await message.reply_text(
            "📁 **File Processing**\n\n"
            "The auto rename feature is currently initializing.\n"
            "Please try again in a moment."
        )
    
    auto_rename_files_func = fallback_auto_rename

# Create wrapper function
async def safe_auto_rename_files(client, message):
    """Wrapper for auto rename with error handling"""
    if auto_rename_files_func:
        try:
            await auto_rename_files_func(client, message)
        except Exception as e:
            logger.error(f"Error in auto rename: {e}")
            await message.reply_text(f"❌ Error: {str(e)[:200]}")
    else:
        await message.reply_text("❌ Auto rename feature is not available.")

# ===== AUTO RENAME COMMAND =====

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message):
    user_id = message.from_user.id
    
    # Get current mode
    current_mode = await codeflixbots.get_mode(user_id)
    
    # Extract and validate the format from the command
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2 or not command_parts[1].strip():
        await message.reply_text(
            "**Please provide a new name after the command /autorename**\n\n"
            f"**Current Mode:** `{current_mode.replace('_', ' ').title()}`\n"
            "**File Mode:** Extracts from file name\n"
            "**Caption Mode:** Extracts from file caption\n"
            "Use /mode to switch modes\n\n"
            "Here's how to use it:\n"
            "**Example format:** ` /autorename S[SE.NUM]EP[EP.NUM] your video title [QUALITY]`\n\n"
            "**Available Variables:**\n"
            "• `[SE.NUM]` or `{season}` - Season number\n"
            "• `[EP.NUM]` or `{episode}` - Episode number\n"
            "• `[QUALITY]` or `{quality}` - Video quality\n"
            "• `[filename]` - Original filename\n"
            "• `[filesize]` - File size\n"
            "• `[duration]` - Video duration"
        )
        return

    format_template = command_parts[1].strip()

    # Save the format template in the database
    await codeflixbots.set_format_template(user_id, format_template)

    # Send confirmation message
    await message.reply_text(
        f"**🌟 Auto Rename Format Saved!**\n\n"
        f"**Mode:** `{current_mode.replace('_', ' ').title()}`\n"
        f"**Your Template:** `{format_template}`\n\n"
        "📩 **Now send your files and I'll rename them automatically!**\n\n"
        "💡 **Tip:** Use `/mode` to switch between file name and caption extraction."
    )

# ===== SET MEDIA COMMAND =====

@Client.on_message(filters.private & filters.command("setmedia"))
async def set_media_command(client, message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Document", callback_data="setmedia_document")],
        [InlineKeyboardButton("🎥 Video", callback_data="setmedia_video")],
        [InlineKeyboardButton("🎵 Audio", callback_data="setmedia_audio")]
    ])

    await message.reply_text(
        "**📁 Select Media Type:**\n"
        "• **Document:** Send as Telegram document\n"
        "• **Video:** Send as Telegram video\n"
        "• **Audio:** Send as Telegram audio\n\n"
        "This affects how the file will be sent back to you.",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^setmedia_"))
async def handle_media_selection(client, callback_query):
    user_id = callback_query.from_user.id
    media_type = callback_query.data.split("_", 1)[1]

    await codeflixbots.set_media_preference(user_id, media_type)
    await callback_query.answer(f"✅ Set to: {media_type}")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Settings", callback_data="help")]
    ])
    
    await callback_query.message.edit_text(
        f"**✅ Media preference saved!**\n\n"
        f"All renamed files will be sent as: **{media_type}**\n\n"
        "You can change this anytime using `/setmedia`",
        reply_markup=keyboard
    )

# ===== INFO COMMAND FUNCTIONS =====

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    for unit in units:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def format_duration(seconds):
    """Convert seconds to HH:MM:SS format"""
    if seconds == 0:
        return "00:00:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

async def extract_media_info(file_path):
    """Extract media information using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode()[:200] if stderr else "Unknown error"
            logger.error(f"FFprobe error: {error_msg}")
            return None
        
        import json
        return json.loads(stdout.decode())
    except Exception as e:
        logger.error(f"Error extracting media info: {e}")
        return None

def format_media_info_output(media_info, filename, file_size, user_name):
    """Format media information into a readable message"""
    if not media_info:
        return "❌ Unable to extract media information from this file."
    
    try:
        format_info = media_info.get('format', {})
        streams = media_info.get('streams', [])
        
        # Current date
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Format output
        output = []
        output.append(f"**📊 Media Information**\n")
        output.append(f"━━━━━━━━━━━━━━━━━━━━\n")
        output.append(f"📁 **File:** `{filename}`")
        output.append(f"🗓️ **Date:** {current_date}")
        output.append(f"👤 **Requested by:** {user_name}")
        output.append(f"📦 **Size:** {format_file_size(file_size)}\n")
        
        # General Information
        output.append("**📌 General Information**")
        output.append(f"• Format: `{format_info.get('format_name', 'N/A')}`")
        output.append(f"• Duration: `{format_duration(float(format_info.get('duration', 0)))}`")
        
        bit_rate = format_info.get('bit_rate', '0')
        if bit_rate != '0':
            bit_rate_kbps = int(bit_rate) // 1000
            output.append(f"• Bitrate: `{bit_rate_kbps} kb/s`")
        
        # Video streams
        video_streams = [s for s in streams if s['codec_type'] == 'video']
        if video_streams:
            output.append(f"\n**🎬 Video Streams: {len(video_streams)}**")
            for idx, video in enumerate(video_streams, 1):
                output.append(f"\n**Video #{idx}**")
                output.append(f"  Codec: `{video.get('codec_name', 'N/A')}`")
                width = video.get('width', 'N/A')
                height = video.get('height', 'N/A')
                if width != 'N/A' and height != 'N/A':
                    output.append(f"  Resolution: `{width}x{height}`")
                
                frame_rate = video.get('r_frame_rate', 'N/A')
                if frame_rate != 'N/A':
                    try:
                        num, den = map(int, frame_rate.split('/'))
                        fps = num / den if den != 0 else num
                        output.append(f"  FPS: `{fps:.3f}`")
                    except:
                        output.append(f"  FPS: `{frame_rate}`")
        
        # Audio streams
        audio_streams = [s for s in streams if s['codec_type'] == 'audio']
        if audio_streams:
            output.append(f"\n**🎵 Audio Streams: {len(audio_streams)}**")
            for idx, audio in enumerate(audio_streams, 1):
                output.append(f"\n**Audio #{idx}**")
                output.append(f"  Codec: `{audio.get('codec_name', 'N/A')}`")
                output.append(f"  Channels: `{audio.get('channels', 'N/A')}`")
                output.append(f"  Sample Rate: `{audio.get('sample_rate', 'N/A')} Hz`")
                
                # Language
                audio_tags = audio.get('tags', {})
                language = audio_tags.get('language', audio_tags.get('LANGUAGE', 'Unknown'))
                output.append(f"  Language: `{language}`")
        
        # Subtitle streams
        subtitle_streams = [s for s in streams if s['codec_type'] == 'subtitle']
        if subtitle_streams:
            output.append(f"\n**💬 Subtitle Streams: {len(subtitle_streams)}**")
            for idx, subtitle in enumerate(subtitle_streams, 1):
                output.append(f"\n**Subtitle #{idx}**")
                output.append(f"  Format: `{subtitle.get('codec_name', 'N/A')}`")
                
                # Language
                subtitle_tags = subtitle.get('tags', {})
                language = subtitle_tags.get('language', subtitle_tags.get('LANGUAGE', 'Unknown'))
                output.append(f"  Language: `{language}`")
        
        output.append(f"\n━━━━━━━━━━━━━━━━━━━━")
        output.append(f"ℹ️ Use `/autorename` to set up automatic renaming")
        
        return "\n".join(output)
    
    except Exception as e:
        logger.error(f"Error formatting media info: {e}")
        return f"❌ Error processing media information:\n`{str(e)[:200]}`"

@Client.on_message(filters.private & filters.command("info"))
async def info_command(client, message):
    """Handle /info command - temporarily disable auto rename and get file info"""
    user_id = message.from_user.id
    
    # Exit if already in info mode
    if user_id in info_mode_users:
        del info_mode_users[user_id]
        await message.reply_text("ℹ️ Exited info mode.")
        return
    
    # Set user to info mode
    info_mode_users[user_id] = {
        "active": True,
        "message_id": message.id,
        "start_time": datetime.now()
    }
    
    # Ask user to send a file
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Exit Info Mode", callback_data="exit_info_mode")]
    ])
    
    await message.reply_text(
        "**📋 File Information Mode**\n\n"
        "📁 Please send me a file (video/document) to analyze.\n"
        "I will extract and display detailed media information.\n\n"
        "⚠️ **Note:** Auto-rename is temporarily disabled in this mode.\n"
        "Send `/info` again or click the button below to exit.\n\n"
        "✨ **Supported formats:** MP4, MKV, AVI, MOV, etc.",
        reply_markup=buttons
    )

@Client.on_callback_query(filters.regex("^exit_info_mode$"))
async def exit_info_mode_callback(client, callback_query):
    """Handle exit button for /info mode"""
    user_id = callback_query.from_user.id
    
    if user_id in info_mode_users:
        del info_mode_users[user_id]
        await callback_query.answer("Exited info mode")
    
    await callback_query.message.edit_text(
        "✅ **Info mode exited.**\n\n"
        "Auto-rename is now active again.\n"
        "Send `/info` to analyze another file.",
        reply_markup=None
    )

async def process_file_for_info(client, message):
    """Process file sent during /info mode"""
    user_id = message.from_user.id
    
    processing_msg = await message.reply_text("🔍 **Analyzing file...**\n\nPlease wait, this may take a moment.")
    
    # Get file details
    if message.document:
        filename = message.document.file_name or "document"
        file_size = message.document.file_size or 0
    elif message.video:
        filename = message.video.file_name or f"video_{message.id}.mp4"
        file_size = message.video.file_size or 0
    elif message.audio:
        filename = message.audio.file_name or f"audio_{message.id}.mp3"
        file_size = message.audio.file_size or 0
    else:
        await processing_msg.edit_text("❌ Unsupported file type.")
        return
    
    # Create temp directory
    temp_dir = "temp_info_files"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{user_id}_{message.id}_{filename}")
    
    try:
        # Download the file
        await processing_msg.edit_text("📥 **Downloading file...**")
        
        file_path = await client.download_media(
            message,
            file_name=temp_path
        )
        
        if not file_path or not os.path.exists(file_path):
            await processing_msg.edit_text("❌ Failed to download file.")
            return
        
        # Extract media info
        await processing_msg.edit_text("📊 **Extracting information...**")
        media_info = await extract_media_info(file_path)
        
        if media_info:
            # Format the output
            user_name = message.from_user.first_name or "User"
            info_output = format_media_info_output(media_info, filename, file_size, user_name)
            
            # Send the info
            await processing_msg.delete()
            
            # Split if too long
            if len(info_output) > 4000:
                # Send in parts
                parts = []
                current = ""
                for line in info_output.split('\n'):
                    if len(current) + len(line) + 1 < 4000:
                        current += line + '\n'
                    else:
                        parts.append(current)
                        current = line + '\n'
                if current:
                    parts.append(current)
                
                # Send first part
                first_msg = await message.reply_text(
                    parts[0],
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
                
                # Send remaining parts
                for part in parts[1:]:
                    await message.reply_text(
                        part,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True
                    )
            else:
                await message.reply_text(
                    info_output,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
        else:
            await processing_msg.edit_text(
                "❌ **Unable to extract information.**\n\n"
                "Possible reasons:\n"
                "• File is corrupted\n"
                "• Unsupported format\n"
                "• FFmpeg not installed\n\n"
                "Try another file or check the format."
            )
        
    except Exception as e:
        logger.error(f"Error in info mode processing: {e}")
        await processing_msg.edit_text(f"❌ **Error:** {str(e)[:200]}")
    
    finally:
        # Clean up
        try:
            if 'file_path' in locals() and file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up temp file: {e}")
        
        # Remove from info mode (single use)
        if user_id in info_mode_users:
            del info_mode_users[user_id]

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_file_upload(client, message):
    """Main handler for uploaded files - routes to info mode or auto rename"""
    user_id = message.from_user.id
    
    # Check if user is in info mode
    if user_id in info_mode_users and info_mode_users[user_id]["active"]:
        # Process for info mode
        await process_file_for_info(client, message)
    else:
        # Process for auto rename using the wrapper
        await safe_auto_rename_files(client, message)

@Client.on_message(filters.private & filters.command("exit_info"))
async def exit_info_command(client, message):
    """Command to exit info mode"""
    user_id = message.from_user.id
    
    if user_id in info_mode_users:
        del info_mode_users[user_id]
        await message.reply_text("✅ Exited info mode. Auto-rename is now active.")
    else:
        await message.reply_text("ℹ️ You are not in info mode.")

# Background cleanup task
async def cleanup_old_sessions():
    """Clean up old info mode sessions"""
    while True:
        try:
            await asyncio.sleep(300)  # Check every 5 minutes
            
            current_time = datetime.now()
            to_remove = []
            
            for user_id, data in info_mode_users.items():
                if (current_time - data["start_time"]).total_seconds() > 600:  # 10 minutes
                    to_remove.append(user_id)
            
            for user_id in to_remove:
                if user_id in info_mode_users:
                    del info_mode_users[user_id]
                    logger.info(f"Cleaned up old info session for user {user_id}")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)

# Start cleanup task when module loads
import threading

def start_cleanup_background():
    """Start cleanup task in background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(cleanup_old_sessions())

# Start background cleanup thread
cleanup_thread = threading.Thread(target=start_cleanup_background, daemon=True)
cleanup_thread.start()
logger.info("Started background cleanup thread for info mode sessions")

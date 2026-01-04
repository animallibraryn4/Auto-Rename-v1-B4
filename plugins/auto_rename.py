
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import codeflixbots
import os
import asyncio
import subprocess
import tempfile
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode

# Import the auto_rename_files function from file_rename.py
from plugins.file_rename import auto_rename_files
info_mode_users = {}


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
            "**Example format:** ` /autorename S[SE.NUM]EP[EP.NUM] your video title [QUALITY]`"
        )
        return

    format_template = command_parts[1].strip()

    # Save the format template in the database
    await codeflixbots.set_format_template(user_id, format_template)

    # Send confirmation message with the template in monospaced font
    await message.reply_text(
        f"**🌟 Fantastic! You're ready to auto-rename your files.**\n\n"
        f"**Current Mode:** `{current_mode.replace('_', ' ').title()}`\n\n"
        f"📩 Simply send the file(s) you want to rename.\n\n"
        f"**Your saved template:** `{format_template}`\n\n"
        "Remember, it might take some time, but I'll ensure your files are renamed perfectly!✨"
    )


@Client.on_message(filters.private & filters.command("setmedia"))
async def set_media_command(client, message):
    # Define inline keyboard buttons for media type selection
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Document", callback_data="setmedia_document")],
        [InlineKeyboardButton("🎥 Video", callback_data="setmedia_video")]
    ])

    # Send a message with the inline buttons
    await message.reply_text(
        "**Please select the media type you want to set:**",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("^setmedia_"))
async def handle_media_selection(client, callback_query):
    user_id = callback_query.from_user.id
    media_type = callback_query.data.split("_", 1)[1]  # Extract media type from callback data

    # Save the preferred media type in the database
    await codeflixbots.set_media_preference(user_id, media_type)

    # Acknowledge the callback and send confirmation
    await callback_query.answer(f"Media preference set to: {media_type} ✅")
    await callback_query.message.edit_text(f"**Media preference set to:** {media_type} ✅")

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def format_duration(seconds):
    """Convert seconds to HH:MM:SS format"""
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
            return None
        
        import json
        return json.loads(stdout.decode())
    except Exception as e:
        print(f"Error extracting media info: {e}")
        return None

def format_media_info_output(media_info, filename, user_name):
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
        output.append(f"**MediaInfo - {filename}**")
        output.append(f"_{current_date}_\n")
        output.append("📄 **MediaInfo**\n")
        output.append(f"🗓 **Date:** {current_date}")
        output.append(f"👤 **By:** {user_name}")
        output.append(f"📁 **File:** {filename}\n")
        
        # General Information
        output.append("📌 **General**")
        output.append(f"Complete name: {format_info.get('filename', 'N/A')}")
        output.append(f"Format: {format_info.get('format_name', 'N/A')}")
        output.append(f"Format version: {format_info.get('format_version', 'N/A')}")
        output.append(f"File size: {format_file_size(float(format_info.get('size', 0)))}")
        
        duration = float(format_info.get('duration', 0))
        output.append(f"Duration: {format_duration(duration)}")
        
        bit_rate = format_info.get('bit_rate', 'N/A')
        if bit_rate != 'N/A':
            bit_rate_kbps = int(bit_rate) // 1000
            output.append(f"Overall bit rate: {bit_rate_kbps} kb/s")
        else:
            output.append(f"Overall bit rate: N/A")
        
        tags = format_info.get('tags', {})
        writing_app = tags.get('writing_application', tags.get('ENCODER', 'N/A'))
        writing_lib = tags.get('writing_library', tags.get('ENCODER_LIBRARY', 'N/A'))
        
        output.append(f"Writing application: {writing_app}")
        output.append(f"Writing library: {writing_lib}\n")
        
        # Process streams
        video_streams = [s for s in streams if s['codec_type'] == 'video']
        audio_streams = [s for s in streams if s['codec_type'] == 'audio']
        subtitle_streams = [s for s in streams if s['codec_type'] == 'subtitle']
        
        # Video streams
        for idx, video in enumerate(video_streams, 1):
            output.append(f"🎞 **Video #{idx}**")
            output.append(f"ID: {video.get('index', idx)}")
            output.append(f"Format: {video.get('codec_name', 'N/A')}")
            output.append(f"Format/Info: {video.get('codec_long_name', 'N/A')}")
            output.append(f"Format profile: {video.get('profile', 'N/A')}")
            output.append(f"Codec ID: {video.get('codec_tag_string', 'N/A')}")
            
            if 'duration' in video:
                output.append(f"Duration: {format_duration(float(video['duration']))}")
            
            width = video.get('width', 'N/A')
            height = video.get('height', 'N/A')
            if width != 'N/A' and height != 'N/A':
                output.append(f"Resolution: {width}x{height} pixels")
            
            display_aspect_ratio = video.get('display_aspect_ratio', 'N/A')
            output.append(f"Display aspect ratio: {display_aspect_ratio}")
            
            frame_rate = video.get('r_frame_rate', 'N/A')
            if frame_rate != 'N/A':
                try:
                    num, den = map(int, frame_rate.split('/'))
                    fps = num / den if den != 0 else num
                    output.append(f"Frame rate: {fps:.3f}")
                except:
                    output.append(f"Frame rate: {frame_rate}")
            
            color_space = video.get('color_space', 'N/A')
            output.append(f"Color space: {color_space}")
            
            pix_fmt = video.get('pix_fmt', 'N/A')
            output.append(f"Pixel format: {pix_fmt}")
            
            bit_depth = video.get('bits_per_raw_sample', video.get('bits_per_sample', 'N/A'))
            output.append(f"Bit depth: {bit_depth}")
            
            # Video tags
            video_tags = video.get('tags', {})
            writing_library = video_tags.get('encoder', video_tags.get('ENCODER', 'N/A'))
            output.append(f"Writing library: {writing_library}\n")
        
        # Audio streams
        for idx, audio in enumerate(audio_streams, 1):
            output.append(f"🔊 **Audio #{idx}**")
            output.append(f"ID: {audio.get('index', len(video_streams) + idx)}")
            output.append(f"Format: {audio.get('codec_name', 'N/A')}")
            output.append(f"Codec ID: {audio.get('codec_tag_string', 'N/A')}")
            
            if 'duration' in audio:
                output.append(f"Duration: {format_duration(float(audio['duration']))}")
            
            channels = audio.get('channels', 'N/A')
            output.append(f"Channel(s): {channels}")
            
            channel_layout = audio.get('channel_layout', 'N/A')
            output.append(f"Channel layout: {channel_layout}")
            
            sample_rate = audio.get('sample_rate', 'N/A')
            output.append(f"Sampling rate: {sample_rate}")
            
            bit_rate = audio.get('bit_rate', 'N/A')
            if bit_rate != 'N/A':
                bit_rate_kbps = int(bit_rate) // 1000
                output.append(f"Bit rate: {bit_rate_kbps} kb/s")
            
            # Audio tags
            audio_tags = audio.get('tags', {})
            title = audio_tags.get('title', audio_tags.get('TITLE', 'N/A'))
            language = audio_tags.get('language', audio_tags.get('LANGUAGE', 'N/A'))
            default = "Yes" if audio.get('disposition', {}).get('default', 0) == 1 else "No"
            forced = "Yes" if audio.get('disposition', {}).get('forced', 0) == 1 else "No"
            
            output.append(f"Title: {title}")
            output.append(f"Language: {language}")
            output.append(f"Default: {default}")
            output.append(f"Forced: {forced}\n")
        
        # Subtitle streams
        for idx, subtitle in enumerate(subtitle_streams, 1):
            output.append(f"💬 **Subtitle #{idx}**")
            output.append(f"ID: {subtitle.get('index', len(video_streams) + len(audio_streams) + idx)}")
            output.append(f"Format: {subtitle.get('codec_name', 'N/A')}")
            output.append(f"Codec ID: {subtitle.get('codec_tag_string', 'N/A')}")
            
            codec_long_name = subtitle.get('codec_long_name', 'N/A')
            if 'PGS' in codec_long_name:
                output.append(f"Codec ID/Info: Picture based subtitle format used on BDs/HD-DVDs")
            
            # Subtitle tags
            subtitle_tags = subtitle.get('tags', {})
            language = subtitle_tags.get('language', subtitle_tags.get('LANGUAGE', 'N/A'))
            default = "Yes" if subtitle.get('disposition', {}).get('default', 0) == 1 else "No"
            forced = "Yes" if subtitle.get('disposition', {}).get('forced', 0) == 1 else "No"
            
            output.append(f"Language: {language}")
            output.append(f"Default: {default}")
            output.append(f"Forced: {forced}\n")
        
        return "\n".join(output)
    
    except Exception as e:
        print(f"Error formatting media info: {e}")
        return f"❌ Error processing media information: {str(e)}"

@Client.on_message(filters.private & filters.command("info"))
async def info_command(client, message):
    """Handle /info command - temporarily disable auto rename and get file info"""
    user_id = message.from_user.id
    
    # Set user to info mode
    info_mode_users[user_id] = {
        "active": True,
        "message_id": message.id
    }
    
    # Ask user to send a file
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_info")]
    ])
    
    await message.reply_text(
        "📋 **File Information Mode**\n\n"
        "Please send me a file (video/document) to analyze.\n"
        "I will extract and display detailed media information.\n\n"
        "⚠️ **Note:** Auto rename is temporarily disabled while in this mode.\n"
        "Send any other command to exit this mode.",
        reply_markup=buttons
    )

@Client.on_callback_query(filters.regex("^cancel_info$"))
async def cancel_info_callback(client, callback_query):
    """Handle cancel button for /info mode"""
    user_id = callback_query.from_user.id
    
    if user_id in info_mode_users:
        del info_mode_users[user_id]
    
    await callback_query.message.edit_text(
        "❌ File information mode cancelled.",
        reply_markup=None
    )
    await callback_query.answer("Cancelled")

@Client.on_message(filters.private & (filters.document | filters.video))
async def handle_info_mode_file(client, message):
    """Handle file sent during /info mode"""
    user_id = message.from_user.id
    
    # Check if user is in info mode
    if user_id not in info_mode_users or not info_mode_users[user_id]["active"]:
        # Not in info mode, proceed with normal auto rename
        return await auto_rename_files(client, message)
    
    # User is in info mode, process file for info
    processing_msg = await message.reply_text("🔍 Analyzing file... Please wait.")
    
    try:
        # Download the file
        download_path = f"temp_info_{user_id}_{message.id}"
        
        file_path = await client.download_media(
            message,
            file_name=download_path
        )
        
        if not file_path or not os.path.exists(file_path):
            await processing_msg.edit_text("❌ Failed to download file.")
            return
        
        # Get file name
        if message.document:
            filename = message.document.file_name
        elif message.video:
            filename = message.video.file_name or f"video_{message.id}.mp4"
        else:
            filename = "unknown_file"
        
        # Extract media info
        await processing_msg.edit_text("📊 Extracting media information...")
        media_info = await extract_media_info(file_path)
        
        if media_info:
            # Format the output
            user_name = message.from_user.first_name or "User"
            info_output = format_media_info_output(media_info, filename, user_name)
            
            # Send the info (split if too long)
            if len(info_output) > 4096:
                # Split into multiple messages
                parts = []
                current_part = ""
                
                for line in info_output.split('\n'):
                    if len(current_part) + len(line) + 1 < 4096:
                        current_part += line + '\n'
                    else:
                        parts.append(current_part)
                        current_part = line + '\n'
                
                if current_part:
                    parts.append(current_part)
                
                # Send first part
                await processing_msg.delete()
                first_msg = await message.reply_text(
                    parts[0],
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Send remaining parts
                for part in parts[1:]:
                    await message.reply_text(
                        part,
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                await processing_msg.delete()
                await message.reply_text(
                    info_output,
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await processing_msg.edit_text(
                "❌ Unable to extract media information from this file.\n"
                "The file might be corrupted or in an unsupported format."
            )
        
    except Exception as e:
        print(f"Error in info mode: {e}")
        await processing_msg.edit_text(f"❌ Error processing file: {str(e)}")
    
    finally:
        # Clean up
        if user_id in info_mode_users:
            del info_mode_users[user_id]
        
        # Remove downloaded file
        if 'file_path' in locals() and file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

@Client.on_message(filters.private & filters.command)
async def check_info_mode_exit(client, message):
    """Exit info mode if any other command is sent"""
    user_id = message.from_user.id
    
    # Check if user is in info mode and command is not /info
    if user_id in info_mode_users and not message.command[0] == "info":
        # Exit info mode
        del info_mode_users[user_id]
        await message.reply_text("ℹ️ Info mode exited. Auto rename is now active again.")

@Client.on_message(filters.private & (filters.document | filters.video))
async def handle_info_mode_file(client, message):
    """Handle file sent during /info mode"""
    user_id = message.from_user.id
    
    # DEBUG: Check if info mode is working
    print(f"DEBUG: User {user_id} sending file. Info mode status: {user_id in info_mode_users}")
    
    # Check if user is in info mode
    if user_id not in info_mode_users or not info_mode_users[user_id].get("active", False):
        # Not in info mode, proceed with normal auto rename
        print(f"DEBUG: User {user_id} not in info mode, calling auto_rename_files")
        return await auto_rename_files(client, message)
    
    print(f"DEBUG: User {user_id} is in info mode, processing file for info")
    # Rest of the function remains the same...

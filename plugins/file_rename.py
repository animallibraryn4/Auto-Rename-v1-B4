import os
import re
import time
import shutil
import asyncio
import logging
from datetime import datetime
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from plugins.antinsfw import check_anti_nsfw
from helper.utils import progress_for_pyrogram, humanbytes, convert
from helper.database import codeflixbots
from config import Config
from plugins import is_user_verified, send_verification
from plugins.auto_rename import info_mode_users
from plugins.sequence import user_sequences
import collections

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== FIXED SILENT QUEUE SYSTEM =====
# Global dictionaries for queue management
user_queues = {}  # user_id -> asyncio.Queue
user_workers = {}  # user_id -> worker task
user_file_order = {}  # user_id -> [file_ids in order]
user_currently_processing = {}  # user_id -> bool
user_lock = {}  # user_id -> asyncio.Lock

# Cleanup old queue system variables
if 'renaming_operations' in globals():
    del renaming_operations
if 'recent_verification_checks' in globals():
    recent_verification_checks = {}
else:
    recent_verification_checks = {}

# ===== ORIGINAL FUNCTIONS (Keep all your existing functions) =====
# Make sure these are included from your original file:

def standardize_quality_name(quality):
    """Restored and Improved: Standardize quality names for consistent storage"""
    if not quality or quality == "Unknown":
        return "Unknown"
        
    q = quality.lower().strip()
    if any(x in q for x in ['4k', '2160', 'uhd']): return '2160p'
    if any(x in q for x in ['2k', '1440', 'qhd']): return '1440p'
    if '1080' in q: return '1080p'
    if '720' in q: return '720p'
    if '480' in q: return '480p'
    if '360' in q: return '360p'
    if any(x in q for x in ['hdrip', 'hd', 'web-dl']): return 'HDrip'
    if '4kx264' in q: return '4kX264'
    if '4kx265' in q: return '4kx265'
    
    match = re.search(r'(\d{3,4}p)', q)
    if match: return match.group(1)
    
    return quality.capitalize()

async def convert_ass_subtitles(input_path, output_path):
    """Convert ASS subtitles to mov_text format for MP4 compatibility"""
    ffmpeg_cmd = shutil.which('ffmpeg')
    if ffmpeg_cmd is None:
        raise Exception("FFmpeg not found")
    
    command = [
        ffmpeg_cmd,
        '-i', input_path,
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-c:s', 'mov_text',
        '-map', '0',
        '-loglevel', 'error',
        '-y',
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_message = stderr.decode()
        raise Exception(f"Subtitle conversion failed: {error_message}")

async def convert_to_mkv(input_path, output_path):
    """Convert any video file to MKV format without re-encoding"""
    ffmpeg_cmd = shutil.which('ffmpeg')
    if ffmpeg_cmd is None:
        raise Exception("FFmpeg not found")
    
    command = [
        ffmpeg_cmd,
        '-i', input_path,
        '-map', '0',
        '-c', 'copy',
        '-loglevel', 'error',
        '-y',
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_message = stderr.decode()
        raise Exception(f"MKV conversion failed: {error_message}")

def extract_quality(text):
    """Extract quality from text with enhanced caption support"""
    # Enhanced patterns for caption mode
    caption_quality_patterns = [
        (re.compile(r'(?:quality|resolution|res|qualit[ée])\s*[:=-]?\s*(\d{3,4}[^\dp]*p)', re.IGNORECASE), 
         lambda m: m.group(1)),
        (re.compile(r'(?:quality|resolution|res|qualit[ée])\s*[:=-]?\s*(\d{3,4}p)', re.IGNORECASE), 
         lambda m: m.group(1)),
        (re.compile(r'\b(?:HD|Full HD|FHD|UHD|4K|2K|HDR|HDRip)\b', re.IGNORECASE),
         lambda m: m.group(0)),
    ]
    
    # Try caption-specific patterns first
    for pattern, quality in caption_quality_patterns:
        match = re.search(pattern, text)
        if match:
            return quality(match) if callable(quality) else quality
    
    # Then try standard patterns
    pattern5 = re.compile(r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', re.IGNORECASE)
    pattern6 = re.compile(r'[([<{]?\s*4k\s*[)\]>}]?', re.IGNORECASE)
    pattern7 = re.compile(r'[([<{]?\s*2k\s*[)\]>}]?', re.IGNORECASE)
    pattern8 = re.compile(r'[([<{]?\s*HdRip\s*[)\]>}]?|\bHdRip\b', re.IGNORECASE)
    pattern9 = re.compile(r'[([<{]?\s*4kX264\s*[)\]>}]?', re.IGNORECASE)
    pattern10 = re.compile(r'[([<{]?\s*4kx265\s*[)]>}]?', re.IGNORECASE)
    
    for pattern, quality in [(pattern5, lambda m: m.group(1) or m.group(2)), 
                            (pattern6, "4k"), 
                            (pattern7, "2k"), 
                            (pattern8, "HdRip"), 
                            (pattern9, "4kX264"), 
                            (pattern10, "4kx265")]:
        match = re.search(pattern, text)
        if match: 
            return quality(match) if callable(quality) else quality
    return "Unknown"

# ===== ENHANCED PATTERNS FOR CAPTION MODE =====
pattern_caption_season_verbose = re.compile(
    r'(?:season|saison|sezon|сезон|temporada|сезона|temporada)\s*[:=-]?\s*(\d+)', 
    re.IGNORECASE
)
pattern_caption_episode_verbose = re.compile(
    r'(?:episode|ep|eps|эпизод|cap[íi]tulo|серия|episodio)\s*[:=-]?\s*(\d+)', 
    re.IGNORECASE
)
pattern_caption_season_episode_combined = re.compile(
    r'(?:season|s)\s*[:=-]?\s*(\d+)\s*(?:episode|ep)\s*[:=-]?\s*(\d+)', 
    re.IGNORECASE
)
pattern_caption_simple = re.compile(
    r'(?:season|s)\s*(\d+)\s*(?:episode|ep)\s*(\d+)', 
    re.IGNORECASE
)
pattern_caption_number_pair = re.compile(r'(\d+)\s*(?:[-~]|and|&|,)\s*(\d+)', re.IGNORECASE)

# Original patterns for backward compatibility
pattern1 = re.compile(r'S(\d+)(?:E|EP)(\d+)')
pattern2 = re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)')
pattern3 = re.compile(r'(?:[([<{]?\s*(?:E|EP)\s*(\d+)\s*[)\]>}]?)')
pattern3_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
patternX = re.compile(r'(\d+)')
pattern11 = re.compile(r'Vol(\d+)\s*-\s*Ch(\d+)', re.IGNORECASE)

def extract_season_number(text, is_caption_mode=False):
    """Extract season number from text with enhanced caption support"""
    if not text:
        return None
    
    if is_caption_mode:
        clean_text = re.sub(r'\s+', ' ', text.strip())
        
        match = pattern_caption_season_verbose.search(clean_text)
        if match:
            return match.group(1)
        
        match = pattern_caption_season_episode_combined.search(clean_text)
        if match:
            return match.group(1)
        
        match = pattern_caption_simple.search(clean_text)
        if match:
            return match.group(1)
        
        match = pattern_caption_number_pair.search(clean_text)
        if match:
            if any(keyword in clean_text.lower() for keyword in ['season', 'episode', 'ep', 's', 'e']):
                return match.group(1)
    
    # Fall back to original patterns
    for pattern in [pattern1, pattern4]:
        match = pattern.search(text)
        if match: 
            return match.group(1)
    
    return None

def extract_episode_number(text, is_caption_mode=False):
    """Extract episode number from text with enhanced caption support"""
    if not text:
        return None
    
    if is_caption_mode:
        clean_text = re.sub(r'\s+', ' ', text.strip())
        
        match = pattern_caption_episode_verbose.search(clean_text)
        if match:
            return match.group(1)
        
        match = pattern_caption_season_episode_combined.search(clean_text)
        if match:
            return match.group(2)
        
        match = pattern_caption_simple.search(clean_text)
        if match:
            return match.group(2)
        
        match = pattern_caption_number_pair.search(clean_text)
        if match:
            if any(keyword in clean_text.lower() for keyword in ['season', 'episode', 'ep', 's', 'e']):
                return match.group(2)
    
    # Fall back to original patterns
    for pattern in [pattern1, pattern2, pattern3, pattern3_2, pattern4, patternX]:
        match = pattern.search(text)
        if match: 
            if pattern in [pattern1, pattern2, pattern4]:
                return match.group(2) 
            else:
                return match.group(1)
    
    return None

def extract_volume_chapter(filename):
    match = re.search(pattern11, filename)
    if match:
        return match.group(1), match.group(2)
    return None, None

async def forward_to_dump_channel(client, path, media_type, ph_path, file_name, renamed_file_name, user_info):
    if not Config.DUMP_CHANNEL: 
        return
    try:
        dump_caption = (
            f"➜ **File Renamed**\n\n"
            f"» **User:** {user_info['mention']}\n"
            f"» **User ID:** `{user_info['id']}`\n"
            f"» **Username:** @{user_info['username']}\n\n"
            f"➲ **Original Name:** `{file_name}`\n"
            f"➲ **Renamed To:** `{renamed_file_name}`"
        )
        
        send_func = {
            "document": client.send_document, 
            "video": client.send_video, 
            "audio": client.send_audio
        }.get(media_type, client.send_document)
        
        await send_func(
            Config.DUMP_CHANNEL,
            **{media_type: path},
            file_name=renamed_file_name,
            caption=dump_caption,
            thumb=ph_path if ph_path else None,
        )
    except Exception as e:
        logger.error(f"[DUMP ERROR] {e}")

async def extract_info_from_source(message, user_mode):
    """Extract season, episode, quality from source based on mode"""
    user_id = message.from_user.id
    is_caption_mode = user_mode == "caption_mode"
    
    if user_mode == "file_mode":
        # Extract from file name
        if message.document:
            source_text = message.document.file_name
        elif message.video:
            source_text = message.video.file_name or ""
        elif message.audio:
            source_text = message.audio.file_name or ""
        else:
            return None, None, None, None, None
    else:  # caption_mode
        # Extract from caption
        source_text = message.caption or ""
    
    # Clean and normalize the text for better extraction
    if source_text:
        source_text = re.sub(r'\s+', ' ', source_text.strip())
    
    # Extract season number with mode awareness
    season_number = extract_season_number(source_text, is_caption_mode)
    
    # Extract episode number with mode awareness
    episode_number = extract_episode_number(source_text, is_caption_mode)
    
    # Special handling for common caption patterns
    if is_caption_mode and not episode_number and season_number:
        episode_patterns = [
            r'episode\s*[:=-]?\s*(\d+)',
            r'ep\s*[:=-]?\s*(\d+)',
            r'eps?\s*(\d+)',
            r'e\s*(\d+)',
        ]
        
        for ep_pattern in episode_patterns:
            match = re.search(ep_pattern, source_text, re.IGNORECASE)
            if match:
                episode_number = match.group(1)
                break
    
    # Extract quality
    extracted_quality = extract_quality(source_text)
    standard_quality = standardize_quality_name(extracted_quality) if extracted_quality != "Unknown" else None
    
    # Extract volume and chapter
    volume_number, chapter_number = extract_volume_chapter(source_text)
    
    return season_number, episode_number, standard_quality, volume_number, chapter_number

async def process_rename(client: Client, message: Message):
    """Main file processing function - KEEP YOUR EXISTING CODE"""
    ph_path = None
    
    user_id = message.from_user.id
    if not await is_user_verified(user_id): 
        return

    # Get user's mode preference
    user_mode = await codeflixbots.get_mode(user_id)
    
    format_template = await codeflixbots.get_format_template(user_id)
    media_preference = await codeflixbots.get_media_preference(user_id)
    
    if not format_template:
        return  # Silent return - no message

    # Determine file type and get basic info
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_size = message.document.file_size
        media_type = media_preference or "document"
        is_pdf = message.document.mime_type == "application/pdf"
    elif message.video:
        file_id = message.video.file_id
        file_name = f"{message.video.file_name}.mp4" if message.video.file_name else "video.mp4"
        file_size = message.video.file_size
        media_type = media_preference or "video"
        is_pdf = False
    elif message.audio:
        file_id = message.audio.file_id
        file_name = f"{message.audio.file_name}.mp3" if message.audio.file_name else "audio.mp3"
        file_size = message.audio.file_size
        media_type = media_preference or "audio"
        is_pdf = False
    else:
        return

    # Check for NSFW based on mode
    if user_mode == "file_mode":
        check_text = file_name
    else:
        check_text = message.caption or ""
    
    if await check_anti_nsfw(check_text, message):
        return  # Silent return

    # Extract information based on mode
    season_number, episode_number, standard_quality, volume_number, chapter_number = await extract_info_from_source(message, user_mode)
    
    # Apply extracted information to format template
    if episode_number:
        format_template = format_template.replace("[EP.NUM]", str(episode_number)).replace("{episode}", str(episode_number))
    else:
        format_template = format_template.replace("[EP.NUM]", "").replace("{episode}", "")

    if season_number:
        format_template = format_template.replace("[SE.NUM]", str(season_number)).replace("{season}", str(season_number))
    else:
        format_template = format_template.replace("[SE.NUM]", "").replace("{season}", "")

    if volume_number and chapter_number:
        format_template = format_template.replace("[Vol{volume}]", f"Vol{volume_number}").replace("[Ch{chapter}]", f"Ch{chapter_number}")
    else:
        format_template = format_template.replace("[Vol{volume}]", "").replace("[Ch{chapter}]", "")

    # Extract quality (not for PDFs)
    if not is_pdf and standard_quality:
        format_template = format_template.replace("[QUALITY]", standard_quality).replace("{quality}", standard_quality)
    else:
        format_template = format_template.replace("[QUALITY]", "").replace("{quality}", "")

    # Clean up the format template
    format_template = re.sub(r'\s+', ' ', format_template).strip()
    format_template = format_template.replace("_", " ")
    format_template = re.sub(r'\[\s*\]', '', format_template)

    # Create renamed file name
    _, file_extension = os.path.splitext(file_name)
    renamed_file_name = f"{format_template}{file_extension}"
    
    # Create paths
    download_path = f"downloads/{message.id}_{renamed_file_name}"
    metadata_path = f"Metadata/{message.id}_{renamed_file_name}"
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("Metadata", exist_ok=True)

    download_msg = await message.reply_text("**__Downloading...__**")
    
    try:
        path = await client.download_media(
            message,
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("Download Started...", download_msg, time.time()),
        )
    except Exception as e:
        logger.error(f"Download Error: {e}")
        await download_msg.delete()
        return

    await download_msg.edit("**__Processing File...__**")

    try:
        # MKV Conversion Logic
        need_mkv_conversion = False
        if media_type == "document":
            need_mkv_conversion = True
        elif media_type == "video" and path.lower().endswith('.mp4'):
            need_mkv_conversion = True

        # Convert to MKV if needed
        if need_mkv_conversion and not path.lower().endswith('.mkv'):
            temp_mkv_path = f"{path}.temp.mkv"
            try:
                await convert_to_mkv(path, temp_mkv_path)
                os.remove(path)
                os.rename(temp_mkv_path, path)
                renamed_file_name = f"{format_template}.mkv"
                metadata_path = f"Metadata/{message.id}_{renamed_file_name}"
            except Exception as e:
                await download_msg.edit(f"**MKV Conversion Error:** {e}")
                return

        # SAFE METADATA APPLY
        file_title = await codeflixbots.get_title(user_id)
        artist = await codeflixbots.get_artist(user_id)
        author = await codeflixbots.get_author(user_id)
        video_title = await codeflixbots.get_video(user_id)
        audio_title = await codeflixbots.get_audio(user_id)
        subtitle_title = await codeflixbots.get_subtitle(user_id)

        metadata_command = [
            'ffmpeg',
            '-i', path,
            '-metadata', f'title={file_title}',
            '-metadata', f'artist={artist}',
            '-metadata', f'author={author}',
            '-metadata:s:v', f'title={video_title}',
            '-metadata:s:a', f'title={audio_title}',
            '-metadata:s:s', f'title={subtitle_title}',
            '-map', '0',
            '-c', 'copy',
            '-loglevel', 'error',
            '-y',
            metadata_path
        ]

        process = await asyncio.create_subprocess_exec(
            *metadata_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode()
            await download_msg.edit(f"**Metadata Error:**\n{error_message}")
            return

        path = metadata_path

        upload_msg = await download_msg.edit("**__Uploading...__**")

        # Quality-Based Thumbnail Selection
        c_caption = await codeflixbots.get_caption(message.chat.id)
        c_thumb = None
        is_global_enabled = await codeflixbots.is_global_thumb_enabled(user_id)
 
        if is_global_enabled:
            c_thumb = await codeflixbots.get_global_thumb(user_id)
        else:
            if standard_quality:
                c_thumb = await codeflixbots.get_quality_thumbnail(user_id, standard_quality)
    
            if not c_thumb:
                c_thumb = await codeflixbots.get_thumbnail(user_id)

        if not c_thumb and media_type == "video" and message.video.thumbs:
            c_thumb = message.video.thumbs[0].file_id
 
        caption = (
            c_caption.format(
                filename=renamed_file_name,
                filesize=humanbytes(file_size),
                duration=convert(0),
            )
            if c_caption
            else f"**{renamed_file_name}**"
        )

        # Process thumbnail
        if c_thumb:
            ph_path = await client.download_media(c_thumb)
            if ph_path and os.path.exists(ph_path):
                try:
                    img = Image.open(ph_path).convert("RGB")
                    
                    if media_type == "document":
                        width, height = img.size
                        min_dim = min(width, height)
                        left, top = (width - min_dim) // 2, (height - min_dim) // 2
                        right, bottom = (width + min_dim) // 2, (height + min_dim) // 2
                        img = img.crop((left, top, right, bottom)).resize((320, 320), Image.LANCZOS)
                    else:
                        img.thumbnail((320, 320), Image.LANCZOS)
                    
                    img.save(ph_path, "JPEG", quality=95)
                except Exception as e:
                    logger.error(f"Thumbnail processing error: {e}")
                    ph_path = None

        # Background Forwarding to dump channel
        user_info = {
            'mention': message.from_user.mention, 
            'id': message.from_user.id, 
            'username': message.from_user.username or "No Username"
        }
        asyncio.create_task(forward_to_dump_channel(client, path, media_type, ph_path, file_name, renamed_file_name, user_info))

        # Final Upload
        try:
            if media_type == "document":
                await client.send_document(
                    message.chat.id,
                    document=path,
                    file_name=renamed_file_name,
                    thumb=ph_path,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started...", upload_msg, time.time()),
                )
            elif media_type == "video":
                await client.send_video(
                    message.chat.id,
                    video=path,
                    file_name=renamed_file_name,
                    caption=caption,
                    thumb=ph_path,
                    duration=0,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started...", upload_msg, time.time()),
                )
            elif media_type == "audio":
                await client.send_audio(
                    message.chat.id,
                    audio=path,
                    file_name=renamed_file_name,
                    caption=caption,
                    thumb=ph_path,
                    duration=0,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started...", upload_msg, time.time()),
                )
        except Exception as e:
            os.remove(path)
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
            return await upload_msg.edit(f"Error: {e}")

        await upload_msg.delete()

    except Exception as e:
        logger.error(f"Process Error: {e}")
        await download_msg.delete()
    finally:
        # Clean up files
        for file_path in [download_path, metadata_path, path, ph_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Error removing file {file_path}: {e}")
        
        # Clean up temporary files
        temp_files = [f"{download_path}.temp.mkv"]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

# ===== FIXED SILENT QUEUE WORKER =====
async def user_queue_worker(user_id, client):
    """Worker that processes files in strict FIFO order"""
    try:
        while True:
            # Get the next message from queue
            message = await user_queues[user_id].get()
            
            try:
                # Mark as processing
                user_currently_processing[user_id] = True
                
                # Process the file
                await process_rename(client, message)
                
            except Exception as e:
                logger.error(f"Error processing file for user {user_id}: {e}")
            finally:
                # Mark as done
                user_currently_processing[user_id] = False
                user_queues[user_id].task_done()
                
                # Check if queue is empty and cleanup
                await asyncio.sleep(1)  # Small delay
                if user_id in user_queues and user_queues[user_id].empty():
                    # Wait a bit more to see if new files arrive
                    await asyncio.sleep(5)
                    if user_id in user_queues and user_queues[user_id].empty():
                        # Cleanup
                        if user_id in user_queues:
                            del user_queues[user_id]
                        if user_id in user_workers:
                            del user_workers[user_id]
                        if user_id in user_currently_processing:
                            del user_currently_processing[user_id]
                        if user_id in user_lock:
                            del user_lock[user_id]
                        break
                        
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Worker error for user {user_id}: {e}")
    finally:
        # Cleanup on exit
        for key in [user_queues, user_workers, user_currently_processing, user_lock]:
            key.pop(user_id, None)

# ===== MAIN FILE HANDLER =====
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio), group=-1)
async def auto_rename_files(client, message):
    user_id = message.from_user.id
    
    # ✅ Check if user is in info mode
    if user_id in info_mode_users:
        return
    
    # ✅ Check if user is in sequence mode
    if user_id in user_sequences:
        return
    
    # Check verification
    if not await is_user_verified(user_id):
        curr = time.time()
        if curr - recent_verification_checks.get(user_id, 0) > 2:
            recent_verification_checks[user_id] = curr
            await send_verification(client, message)
        return
    
    # Initialize user lock if not exists
    if user_id not in user_lock:
        user_lock[user_id] = asyncio.Lock()
    
    async with user_lock[user_id]:
        # Initialize queue if not exists
        if user_id not in user_queues:
            user_queues[user_id] = asyncio.Queue()
        
        # Start worker if not running
        if user_id not in user_workers:
            user_workers[user_id] = asyncio.create_task(
                user_queue_worker(user_id, client)
            )
        
        # Track file order
        if user_id not in user_file_order:
            user_file_order[user_id] = []
        
        # Get file ID for tracking
        if message.document:
            file_id = message.document.file_id
        elif message.video:
            file_id = message.video.file_id
        elif message.audio:
            file_id = message.audio.file_id
        else:
            return
        
        user_file_order[user_id].append(file_id)
        
        # Put message in queue (FIFO - First In First Out)
        await user_queues[user_id].put(message)
        
        # Log queue status (silent - no user message)
        queue_size = user_queues[user_id].qsize()
        logger.info(f"User {user_id}: File added to queue. Queue size: {queue_size}")

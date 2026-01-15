import os
import re
import time
import asyncio
import tempfile
from pathlib import Path
from typing import Optional
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from plugins.torrent_handler import torrent_manager
from plugins import __init__ as main_module
from helper.database import n4bots
from config import Config
import logging

logger = logging.getLogger(__name__)

# Import existing functions
from plugins.file_rename import auto_rename_files, queue_manager

async def process_torrent_file(client, message: Message):
    """Process torrent file upload"""
    user_id = message.from_user.id
    
    if user_id not in main_module.user_torrent_state:
        return
    
    state = main_module.user_torrent_state[user_id]
    if state["state"] != "waiting_link":
        return
    
    # Download the torrent file
    temp_dir = tempfile.mkdtemp(prefix="torrent_")
    torrent_path = os.path.join(temp_dir, f"{message.id}.torrent")
    
    download_msg = await message.reply_text("📥 Downloading torrent file...")
    
    try:
        # Download torrent file
        await client.download_media(message, file_name=torrent_path)
        
        if not os.path.exists(torrent_path) or os.path.getsize(torrent_path) == 0:
            await download_msg.edit_text("❌ Failed to download torrent file.")
            return
        
        # Update state
        state["state"] = "processing"
        state["torrent_path"] = torrent_path
        main_module.user_torrent_state[user_id] = state
        
        await download_msg.edit_text("✅ Torrent file downloaded. Processing...")
        
        # Start torrent download
        await handle_torrent_download(client, message, user_id, torrent_path=torrent_path)
        
    except Exception as e:
        logger.error(f"Error processing torrent file: {e}")
        await download_msg.edit_text(f"❌ Error: {str(e)}")
    finally:
        # Clean up
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

async def process_magnet_link(client, message: Message):
    """Process magnet link"""
    user_id = message.from_user.id
    
    if user_id not in main_module.user_torrent_state:
        return
    
    state = main_module.user_torrent_state[user_id]
    if state["state"] != "waiting_link":
        return
    
    magnet_link = message.text.strip()
    
    if not torrent_manager.is_magnet_link(magnet_link):
        await message.reply_text("❌ Invalid magnet link. Please send a valid magnet link starting with 'magnet:'")
        return
    
    # Update state
    state["state"] = "processing"
    state["magnet_link"] = magnet_link
    main_module.user_torrent_state[user_id] = state
    
    download_msg = await message.reply_text("🔗 Processing magnet link...")
    
    # Start torrent download
    await handle_torrent_download(client, message, user_id, magnet_link=magnet_link)

async def handle_torrent_download(client, message: Message, user_id: int, magnet_link: str = None, torrent_path: str = None):
    """Handle torrent downloading process"""
    try:
        progress_msg = await message.reply_text("⏳ Starting torrent download...\n\n"
                                               "This may take some time depending on the file size and seeders.")
        
        # Download torrent content
        downloaded_path = await torrent_manager.download_torrent_content(
            user_id=user_id,
            magnet_link=magnet_link,
            torrent_path=torrent_path
        )
        
        if not downloaded_path or not os.path.exists(downloaded_path):
            await progress_msg.edit_text("❌ Failed to download torrent content.")
            return
        
        # Check if it's a directory (multiple files)
        if os.path.isdir(downloaded_path):
            files = list(Path(downloaded_path).rglob("*"))
            files = [f for f in files if f.is_file()]
            
            if not files:
                await progress_msg.edit_text("❌ No files found in torrent.")
                return
            
            if len(files) == 1:
                # Single file in directory
                file_path = str(files[0])
                await process_downloaded_file(client, message, user_id, file_path, progress_msg)
            else:
                # Multiple files - show selection or process all
                await handle_multiple_files(client, message, user_id, files, progress_msg)
        else:
            # Single file
            await process_downloaded_file(client, message, user_id, downloaded_path, progress_msg)
            
    except Exception as e:
        logger.error(f"Error in torrent download: {e}")
        await message.reply_text(f"❌ Error downloading torrent: {str(e)}")
    finally:
        # Clean up state
        if user_id in main_module.user_torrent_state:
            del main_module.user_torrent_state[user_id]

async def process_downloaded_file(client, message: Message, user_id: int, file_path: str, progress_msg: Message):
    """Process downloaded file through existing auto-rename system"""
    try:
        await progress_msg.edit_text("✅ Download complete! Processing file...")
        
        # Create a fake message object to pass to auto_rename_files
        # This allows us to reuse all existing rename logic
        class FakeMessage:
            def __init__(self, user_id, file_path, client):
                self.from_user = type('obj', (object,), {'id': user_id})()
                self.chat = type('obj', (object,), {'id': user_id})()
                self.id = int(time.time())
                self.document = None
                self.video = None
                self.audio = None
                self.caption = None
                
                # Determine file type and create appropriate attributes
                import mimetypes
                mime_type, _ = mimetypes.guess_type(file_path)
                filename = os.path.basename(file_path)
                
                if mime_type and mime_type.startswith('video/'):
                    self.video = type('obj', (object,), {
                        'file_name': filename,
                        'file_size': os.path.getsize(file_path),
                        'thumbs': None
                    })()
                elif mime_type and mime_type.startswith('audio/'):
                    self.audio = type('obj', (object,), {
                        'file_name': filename,
                        'file_size': os.path.getsize(file_path)
                    })()
                else:
                    self.document = type('obj', (object,), {
                        'file_name': filename,
                        'file_size': os.path.getsize(file_path),
                        'mime_type': mime_type or 'application/octet-stream'
                    })()
                
                # Store actual file path for processing
                self._file_path = file_path
                self._client = client
            
            async def reply_text(self, text, **kwargs):
                return await self._client.send_message(user_id, text, **kwargs)
        
        # Create fake message and process it
        fake_msg = FakeMessage(user_id, file_path, client)
        
        # Use the existing queue manager to process the file
        # This ensures all auto-rename rules, thumbnails, metadata, etc. are applied
        queue_manager.set_client(client)
        await queue_manager.add_to_queue(user_id, fake_msg)
        
        await progress_msg.edit_text("✅ File added to processing queue! It will be renamed and sent to you shortly.")
        
        # Clean up the downloaded file after processing
        # The file will be cleaned up by the existing file_rename.py logic
        
    except Exception as e:
        logger.error(f"Error processing downloaded file: {e}")
        await progress_msg.edit_text(f"❌ Error processing file: {str(e)}")

async def handle_multiple_files(client, message: Message, user_id: int, files: list, progress_msg: Message):
    """Handle torrents with multiple files"""
    try:
        # For simplicity, we'll process each file individually
        await progress_msg.edit_text(f"📁 Found {len(files)} files. Processing each file...")
        
        processed_count = 0
        for file_path in files:
            try:
                await process_downloaded_file(client, message, user_id, str(file_path), None)
                processed_count += 1
                await asyncio.sleep(1)  # Small delay between files
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                continue
        
        await progress_msg.edit_text(f"✅ Processed {processed_count}/{len(files)} files from torrent.")
        
    except Exception as e:
        logger.error(f"Error handling multiple files: {e}")
        await progress_msg.edit_text(f"❌ Error: {str(e)}")

# Message handlers
@Client.on_message(filters.private & filters.document)
async def handle_torrent_file(client, message: Message):
    """Handle .torrent file uploads"""
    user_id = message.from_user.id
    
    if user_id not in main_module.user_torrent_state:
        # Not in torrent mode, let other handlers process it
        return
    
    state = main_module.user_torrent_state.get(user_id)
    if not state or state["state"] != "waiting_link":
        return
    
    # Check if it's a .torrent file
    if message.document:
        filename = message.document.file_name or ""
        if filename.lower().endswith('.torrent'):
            await process_torrent_file(client, message)
            return

@Client.on_message(filters.private & filters.text)
async def handle_magnet_link(client, message: Message):
    """Handle magnet links"""
    user_id = message.from_user.id
    
    if user_id not in main_module.user_torrent_state:
        # Not in torrent mode, let other handlers process it
        return
    
    state = main_module.user_torrent_state.get(user_id)
    if not state or state["state"] != "waiting_link":
        return
    
    text = message.text.strip()
    if text.startswith('magnet:'):
        await process_magnet_link(client, message)
        return

# Cancel torrent command
@Client.on_message(filters.private & filters.command("cancel_torrent"))
async def cancel_torrent_command(client, message: Message):
    """Cancel ongoing torrent download"""
    user_id = message.from_user.id
    
    if user_id in main_module.user_torrent_state:
        del main_module.user_torrent_state[user_id]
        await torrent_manager.cleanup_user_files(user_id)
        await torrent_manager.cleanup_session(user_id)
        await message.reply_text("✅ Torrent download cancelled and cleaned up.")
    else:
        await message.reply_text("❌ No active torrent download to cancel.")

# Clean up on user exit
@Client.on_message(filters.private & filters.command(["start", "help", "autorename"]))
async def cleanup_torrent_state(client, message: Message):
    """Clean up torrent state when user switches to other commands"""
    user_id = message.from_user.id
    if user_id in main_module.user_torrent_state:
        del main_module.user_torrent_state[user_id]
        await torrent_manager.cleanup_user_files(user_id)

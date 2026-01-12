import requests
import os
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.database import n4bots
from plugins.admin_panel import check_ban_status
from plugins import is_user_verified, send_verification

# Allowed file extensions for Catbox (images and common files)
ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',  # Images
    '.mp4', '.mkv', '.mov', '.avi', '.webm',          # Videos
    '.pdf', '.txt', '.zip', '.rar',                   # Documents
}

# Maximum file size: 200MB (Catbox limit)
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB in bytes

async def upload_to_catbox(file_path: str, file_name: str) -> str:
    """
    Upload file to Catbox.moe and return direct URL
    """
    try:
        url = "https://catbox.moe/user/api.php"
        
        # Open file in binary mode
        with open(file_path, 'rb') as file:
            # Prepare form data
            data = {'reqtype': 'fileupload'}
            files = {'fileToUpload': (file_name, file)}
            
            # Upload using requests (synchronous)
            response = requests.post(url, data=data, files=files)
        
        if response.status_code == 200 and response.text.strip():
            return response.text.strip()
        else:
            return None
            
    except Exception as e:
        print(f"Catbox upload error: {e}")
        return None

async def async_upload_to_catbox(file_path: str, file_name: str) -> str:
    """
    Async version of Catbox upload using aiohttp
    """
    try:
        url = "https://catbox.moe/user/api.php"
        
        # Open file
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Prepare form data
        data = aiohttp.FormData()
        data.add_field('reqtype', 'fileupload')
        data.add_field('fileToUpload', 
                      file_content, 
                      filename=file_name,
                      content_type='application/octet-stream')
        
        # Upload using aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.text()
                    return result.strip() if result.strip() else None
                return None
                
    except Exception as e:
        print(f"Async Catbox upload error: {e}")
        return None

@Client.on_message(filters.private & filters.command("catbox"))
async def catbox_upload_command(client: Client, message: Message):
    """
    Handle /catbox command - upload replied media to Catbox
    """
    user_id = message.from_user.id
    
    # ✅ Check if user is banned
    if await check_ban_status(user_id):
        return
    
    # ✅ Check verification
    if not await is_user_verified(user_id):
        await send_verification(client, message)
        return
    
    # Check if message is a reply
    if not message.reply_to_message:
        help_text = """
📤 **Catbox Upload Command**

**Usage:**
1. Send any file (image/video/document)
2. Reply to that file with `/catbox`

**Supported Files:**
• Images: JPG, PNG, GIF, WEBP, BMP
• Videos: MP4, MKV, MOV, AVI, WEBM
• Documents: PDF, TXT, ZIP, RAR

**File Size Limit:** 200MB

**Example:**
Send an image → Reply `/catbox` → Get direct link
        """
        await message.reply_text(help_text)
        return
    
    reply = message.reply_to_message
    
    # Check if replied message contains a file
    if not any([
        reply.photo,
        reply.video,
        reply.document,
        reply.audio,
        reply.animation,
        reply.sticker
    ]):
        await message.reply_text("❌ Please reply to a file (image, video, document, etc.)")
        return
    
    # Get file details
    file_name = None
    file_size = 0
    
    if reply.photo:
        # Photo has multiple sizes, get the largest
        file = reply.photo
        file_name = f"photo_{reply.id}.jpg"
        file_size = file.file_size
    elif reply.video:
        file = reply.video
        file_name = file.file_name or f"video_{reply.id}.mp4"
        file_size = file.file_size
    elif reply.document:
        file = reply.document
        file_name = file.file_name or f"document_{reply.id}"
        file_size = file.file_size
        # Check extension
        if file_name:
            ext = os.path.splitext(file_name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                await message.reply_text(
                    f"❌ Unsupported file type: {ext}\n"
                    f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                )
                return
    elif reply.audio:
        file = reply.audio
        file_name = file.file_name or f"audio_{reply.id}.mp3"
        file_size = file.file_size
    elif reply.animation:
        file = reply.animation
        file_name = f"animation_{reply.id}.gif"
        file_size = file.file_size
    elif reply.sticker:
        file = reply.sticker
        # Stickers need conversion
        if not file.is_animated and not file.is_video:
            file_name = f"sticker_{reply.id}.png"
            file_size = file.file_size
        else:
            await message.reply_text("❌ Animated/video stickers are not supported")
            return
    
    # Check file size
    if file_size > MAX_FILE_SIZE:
        await message.reply_text(f"❌ File too large! Maximum size is 200MB. Your file: {file_size/(1024*1024):.1f}MB")
        return
    
    # Start processing
    processing_msg = await message.reply_text("📥 **Downloading file...**")
    
    # Create temp directory
    temp_dir = "temp_catbox"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Download file
    try:
        file_path = await reply.download(
            file_name=os.path.join(temp_dir, file_name) if file_name else None
        )
        
        if not file_path or not os.path.exists(file_path):
            await processing_msg.edit_text("❌ Failed to download file")
            return
        
        # Get actual file name
        actual_file_name = os.path.basename(file_path)
        
        # Update status
        await processing_msg.edit_text("📤 **Uploading to Catbox...**")
        
        # Upload to Catbox (using async version)
        catbox_url = await async_upload_to_catbox(file_path, actual_file_name)
        
        if catbox_url:
            # Send success message
            success_text = f"""
✅ **Upload Successful!**

📁 **File:** `{actual_file_name}`
🔗 **Direct Link:** {catbox_url}

📋 **Copy Link:**
`{catbox_url}`
            """
            
            # Create inline keyboard with copy button
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_{catbox_url}")],
                [InlineKeyboardButton("🔗 Open Link", url=catbox_url)]
            ])
            
            await processing_msg.edit_text(
                success_text,
                reply_markup=keyboard,
                disable_web_page_preview=False
            )
        else:
            await processing_msg.edit_text("❌ Upload failed. Catbox might be down or the file format is not supported.")
            
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error: {str(e)}")
    
    finally:
        # Clean up temp file
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

@Client.on_callback_query(filters.regex(r"^copy_"))
async def copy_link_callback(client, callback_query):
    """
    Handle copy link button
    """
    url = callback_query.data.split("_", 1)[1]
    
    # Send the URL as a message that user can copy
    await callback_query.message.reply_text(
        f"📋 **Link to copy:**\n\n`{url}`"
    )
    
    await callback_query.answer("Link sent as text - you can copy it now")

@Client.on_message(filters.private & filters.command("catboxhelp"))
async def catbox_help_command(client: Client, message: Message):
    """
    Detailed help for Catbox upload feature
    """
    help_text = """
📤 **Catbox Upload Feature**

**What is Catbox?**
Catbox.moe is a free file hosting service that provides direct links to your uploaded files.

**Commands:**
• `/catbox` - Upload replied file to Catbox
• `/catboxhelp` - Show this help message

**How to use:**
1. Send any supported file to the bot
2. Reply to that file with `/catbox`
3. Get a permanent direct link

**Supported File Types:**
• Images: JPG, PNG, GIF, WEBP, BMP
• Videos: MP4, MKV, MOV, AVI, WEBM (≤200MB)
• Documents: PDF, TXT, ZIP, RAR

**File Size Limit:** 200MB

**Example Workflow:**
1. You: (Send an image)
2. You: `/catbox` (as reply to the image)
3. Bot: `https://files.catbox.moe/x9k3ab.png`

**Features:**
✅ Direct permanent links
✅ No compression for images
✅ Fast upload speeds
✅ No account required
✅ 200MB file size limit
✅ All common file formats
    """
    
    await message.reply_text(help_text, disable_web_page_preview=True)

# Also add info to existing help command
def get_catbox_help_addition():
    return """
📤 **Catbox Upload**
`/catbox` - Upload files to Catbox for direct links
`/catboxhelp` - Detailed Catbox help
    """

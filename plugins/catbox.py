from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import asyncio

@Client.on_message(filters.command("catbox") & filters.private)
async def catbox_upload(client, message):
    # Check if user replied to a message
    if message.reply_to_message:
        # Get the replied message
        reply = message.reply_to_message
        
        # Check if it has media
        if reply.photo or reply.document or reply.video or reply.audio or reply.voice:
            # Download the file
            msg = await message.reply_text("📥 Downloading file...")
            
            # Download file
            file_path = await reply.download()
            
            try:
                # Get file info
                file_size = os.path.getsize(file_path)
                file_name = os.path.basename(file_path)
                
                # Check if file is too large (Catbox limit: 200MB)
                if file_size > 200 * 1024 * 1024:  # 200MB
                    await msg.edit_text("❌ File too large! Catbox max size is 200MB")
                    os.remove(file_path)
                    return
                
                # Try Catbox first
                await msg.edit_text("📤 Uploading to Catbox...")
                
                catbox_success = False
                catbox_url = ""
                
                try:
                    with open(file_path, "rb") as f:
                        response = requests.post(
                            "https://catbox.moe/user/api.php",
                            data={"reqtype": "fileupload"},
                            files={"fileToUpload": f},
                            timeout=60
                        )
                    
                    if response.status_code == 200 and response.text.strip():
                        catbox_url = response.text.strip()
                        if catbox_url.startswith("http"):
                            catbox_success = True
                except:
                    catbox_success = False
                
                # If Catbox failed, try Transfer.sh
                if not catbox_success:
                    await msg.edit_text("⚠️ Catbox failed, trying Transfer.sh...")
                    
                    transfer_success = False
                    transfer_url = ""
                    
                    try:
                        with open(file_path, "rb") as f:
                            response = requests.post(
                                "https://transfer.sh/",
                                files={"file": f},
                                timeout=60
                            )
                        
                        if response.status_code == 200 and response.text.strip():
                            transfer_url = response.text.strip()
                            transfer_success = True
                    except Exception as e:
                        await msg.edit_text(f"⚠️ Transfer.sh failed: {str(e)[:100]}")
                        transfer_success = False
                    
                    if transfer_success:
                        # Send Transfer.sh success
                        buttons = [
                            [InlineKeyboardButton("🔗 Open Link", url=transfer_url)]
                        ]
                        
                        await msg.edit_text(
                            f"✅ **Uploaded to Transfer.sh**\n\n"
                            f"**File:** `{file_name}`\n"
                            f"**Size:** {file_size // 1024} KB\n"
                            f"**Link:** `{transfer_url}`\n\n"
                            f"⚠️ *Note: Link expires in 14 days*",
                            reply_markup=InlineKeyboardMarkup(buttons)
                        )
                        os.remove(file_path)
                        return
                    else:
                        # Last resort: Try 0x0.st
                        await msg.edit_text("⚠️ Trying 0x0.st as last option...")
                        
                        try:
                            with open(file_path, "rb") as f:
                                response = requests.post(
                                    "https://0x0.st",
                                    files={"file": f},
                                    timeout=60
                                )
                            
                            if response.status_code == 200 and response.text.strip():
                                zerozero_url = response.text.strip()
                                buttons = [
                                    [InlineKeyboardButton("🔗 Open Link", url=zerozero_url)]
                                ]
                                
                                await msg.edit_text(
                                    f"✅ **Uploaded to 0x0.st**\n\n"
                                    f"**File:** `{file_name}`\n"
                                    f"**Size:** {file_size // 1024} KB\n"
                                    f"**Link:** `{zerozero_url}`",
                                    reply_markup=InlineKeyboardMarkup(buttons)
                                )
                                os.remove(file_path)
                                return
                        except:
                            pass
                        
                        # All methods failed
                        await msg.edit_text(
                            "❌ **All upload methods failed!**\n\n"
                            "**Possible reasons:**\n"
                            "• Your hosting blocks file uploads\n"
                            "• All file hosts are blocked\n"
                            "• Network issues\n\n"
                            "**Solutions:**\n"
                            "1. Deploy on Koyeb.com (free)\n"
                            "2. Try Railway.app (free credits)\n"
                            "3. Use Replit.com (free)\n"
                            "4. Check bot logs for details"
                        )
                        os.remove(file_path)
                        return
                
                # Catbox success
                short_code = catbox_url.split('/')[-1]
                short_url = f"https://catbox.moe/c/{short_code}"
                
                buttons = [
                    [InlineKeyboardButton("🔗 Direct Link", url=catbox_url)],
                    [InlineKeyboardButton("🌐 Short Link", url=short_url)]
                ]
                
                await msg.edit_text(
                    f"✅ **Upload Successful!**\n\n"
                    f"**File:** `{file_name}`\n"
                    f"**Size:** {file_size // 1024} KB\n"
                    f"**Direct Link:** `{catbox_url}`\n"
                    f"**Short Link:** `{short_url}`",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                    
            except Exception as e:
                await msg.edit_text(f"❌ Error: {str(e)[:150]}")
                
            finally:
                # Clean up downloaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            # Replied message has no media
            await message.reply_text("❌ Please reply to a photo, document, video, audio, or voice message")
    else:
        # No reply - send instructions
        await message.reply_text(
            "**📤 File Upload Bot**\n\n"
            "**How to use:**\n"
            "1. Send any file (photo, document, video, audio)\n"
            "2. Reply to that file with `/catbox`\n\n"
            "**Supported:**\n"
            "• Images (JPG, PNG, GIF)\n"
            "• Documents (PDF, ZIP, etc.)\n"
            "• Videos (MP4, etc.)\n"
            "• Audio files\n"
            "• Voice messages\n\n"
            "**Max size:** 200MB"
        )

# Also handle when user sends file with caption /catbox
@Client.on_message(filters.photo & filters.private)
async def handle_photo_with_caption(client, message):
    # Check if caption contains /catbox command
    if message.caption and "/catbox" in message.caption:
        # Download the file
        msg = await message.reply_text("📥 Downloading file...")
        
        # Download file
        file_path = await message.download()
        
        try:
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            # Check if file is too large (Catbox limit: 200MB)
            if file_size > 200 * 1024 * 1024:  # 200MB
                await msg.edit_text("❌ File too large! Catbox max size is 200MB")
                os.remove(file_path)
                return
            
            # Try Catbox first
            await msg.edit_text("📤 Uploading to Catbox...")
            
            catbox_success = False
            catbox_url = ""
            
            try:
                with open(file_path, "rb") as f:
                    response = requests.post(
                        "https://catbox.moe/user/api.php",
                        data={"reqtype": "fileupload"},
                        files={"fileToUpload": f},
                        timeout=60
                    )
                
                if response.status_code == 200 and response.text.strip():
                    catbox_url = response.text.strip()
                    if catbox_url.startswith("http"):
                        catbox_success = True
            except:
                catbox_success = False
            
            # If Catbox failed, try Transfer.sh
            if not catbox_success:
                await msg.edit_text("⚠️ Catbox failed, trying Transfer.sh...")
                
                transfer_success = False
                transfer_url = ""
                
                try:
                    with open(file_path, "rb") as f:
                        response = requests.post(
                            "https://transfer.sh/",
                            files={"file": f},
                            timeout=60
                        )
                    
                    if response.status_code == 200 and response.text.strip():
                        transfer_url = response.text.strip()
                        transfer_success = True
                except Exception as e:
                    await msg.edit_text(f"⚠️ Transfer.sh failed: {str(e)[:100]}")
                    transfer_success = False
                
                if transfer_success:
                    # Send Transfer.sh success
                    buttons = [
                        [InlineKeyboardButton("🔗 Open Link", url=transfer_url)]
                    ]
                    
                    await msg.edit_text(
                        f"✅ **Uploaded to Transfer.sh**\n\n"
                        f"**File:** `{file_name}`\n"
                        f"**Size:** {file_size // 1024} KB\n"
                        f"**Link:** `{transfer_url}`\n\n"
                        f"⚠️ *Note: Link expires in 14 days*",
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                    os.remove(file_path)
                    return
                else:
                    # Last resort: Try 0x0.st
                    await msg.edit_text("⚠️ Trying 0x0.st as last option...")
                    
                    try:
                        with open(file_path, "rb") as f:
                            response = requests.post(
                                "https://0x0.st",
                                files={"file": f},
                                timeout=60
                            )
                        
                        if response.status_code == 200 and response.text.strip():
                            zerozero_url = response.text.strip()
                            buttons = [
                                [InlineKeyboardButton("🔗 Open Link", url=zerozero_url)]
                            ]
                            
                            await msg.edit_text(
                                f"✅ **Uploaded to 0x0.st**\n\n"
                                f"**File:** `{file_name}`\n"
                                f"**Size:** {file_size // 1024} KB\n"
                                f"**Link:** `{zerozero_url}`",
                                reply_markup=InlineKeyboardMarkup(buttons)
                            )
                            os.remove(file_path)
                            return
                    except:
                        pass
                    
                    # All methods failed
                    await msg.edit_text(
                        "❌ **All upload methods failed!**\n\n"
                        "**Possible reasons:**\n"
                        "• Your hosting blocks file uploads\n"
                        "• All file hosts are blocked\n"
                        "• Network issues\n\n"
                        "**Solutions:**\n"
                        "1. Deploy on Koyeb.com (free)\n"
                        "2. Try Railway.app (free credits)\n"
                        "3. Use Replit.com (free)\n"
                        "4. Check bot logs for details"
                    )
                    os.remove(file_path)
                    return
            
            # Catbox success
            short_code = catbox_url.split('/')[-1]
            short_url = f"https://catbox.moe/c/{short_code}"
            
            buttons = [
                [InlineKeyboardButton("🔗 Direct Link", url=catbox_url)],
                [InlineKeyboardButton("🌐 Short Link", url=short_url)]
            ]
            
            await msg.edit_text(
                f"✅ **Upload Successful!**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {file_size // 1024} KB\n"
                f"**Direct Link:** `{catbox_url}`\n"
                f"**Short Link:** `{short_url}`",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
                
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)[:150]}")
            
        finally:
            # Clean up downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)

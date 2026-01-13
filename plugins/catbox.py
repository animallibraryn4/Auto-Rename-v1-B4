from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os

@Client.on_message(filters.command("catbox") & filters.private)
async def catbox_upload(client, message):
    # Check if user replied to a message
    if message.reply_to_message:
        # Get the replied message
        reply = message.reply_to_message
        
        # Check if it has media
        if reply.photo or reply.document:
            # Download the file
            msg = await message.reply_text("📥 Downloading file...")
            
            # Download file
            file_path = await reply.download()
            
            # Upload to Catbox
            await msg.edit_text("📤 Uploading to Catbox...")
            
            try:
                # Try multiple proxies (choose one that works)
                proxy_list = [
                    # HTTP Proxies
                    {"http": "http://88.99.234.44:3128", "https": "http://88.99.234.44:3128"},
                    {"http": "http://43.134.172.75:3128", "https": "http://43.134.172.75:3128"},
                    {"http": "http://138.68.60.8:3128", "https": "http://138.68.60.8:3128"},
                    # SOCKS5 Proxies (if you install requests[socks])
                    # {"http": "socks5://45.79.221.233:1080", "https": "socks5://45.79.221.233:1080"},
                ]
                
                response = None
                last_error = None
                
                # Try each proxy
                for proxy in proxy_list:
                    try:
                        with open(file_path, "rb") as f:
                            response = requests.post(
                                "https://catbox.moe/user/api.php",
                                data={"reqtype": "fileupload"},
                                files={"fileToUpload": f},
                                proxies=proxy,
                                timeout=30
                            )
                        # If successful, break out of loop
                        if response.status_code == 200:
                            break
                    except Exception as e:
                        last_error = e
                        continue
                
                if response and response.status_code == 200 and response.text.strip():
                    # Success - get the link
                    catbox_url = response.text.strip()
                    
                    # Send success message with button
                    await msg.edit_text(
                        f"✅ Upload Successful",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔗 Open Link", url=catbox_url)]
                        ])
                    )
                else:
                    error_msg = last_error if last_error else "Upload failed"
                    await msg.edit_text(f"❌ Error: {str(error_msg)}")
                    
            except Exception as e:
                await msg.edit_text(f"❌ Error: {str(e)}")
                
            finally:
                # Clean up downloaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            # Replied message has no media
            await message.reply_text("❌ Please reply to an image or file")
    else:
        # No reply - send instructions
        await message.reply_text(
            "**How to use:**\n\n"
            "1. Send an image to the bot\n"
            "2. Reply to that image with `/catbox`\n"
            "3. Wait for the upload\n\n"
            "Or just send an image with caption `/catbox`"
        )

# Also handle when user sends image with caption /catbox
@Client.on_message(filters.photo & filters.private)
async def handle_photo_with_caption(client, message):
    # Check if caption contains /catbox command
    if message.caption and "/catbox" in message.caption:
        # Download the file
        msg = await message.reply_text("📥 Downloading file...")
        
        # Download file
        file_path = await message.download()
        
        # Upload to Catbox
        await msg.edit_text("📤 Uploading to Catbox...")
        
        try:
            # Try multiple proxies (choose one that works)
            proxy_list = [
                {"http": "http://88.99.234.44:3128", "https": "http://88.99.234.44:3128"},
                {"http": "http://43.134.172.75:3128", "https": "http://43.134.172.75:3128"},
                {"http": "http://138.68.60.8:3128", "https": "http://138.68.60.8:3128"},
            ]
            
            response = None
            last_error = None
            
            # Try each proxy
            for proxy in proxy_list:
                try:
                    with open(file_path, "rb") as f:
                        response = requests.post(
                            "https://catbox.moe/user/api.php",
                            data={"reqtype": "fileupload"},
                            files={"fileToUpload": f},
                            proxies=proxy,
                            timeout=30
                        )
                    # If successful, break out of loop
                    if response.status_code == 200:
                        break
                except Exception as e:
                    last_error = e
                    continue
            
            if response and response.status_code == 200 and response.text.strip():
                # Success - get the link
                catbox_url = response.text.strip()
                
                # Send success message with button
                await msg.edit_text(
                    "✅ Upload Successful",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔗 Open Link", url=catbox_url)]
                    ])
                )
            else:
                error_msg = last_error if last_error else "Upload failed"
                await msg.edit_text(f"❌ Error: {str(error_msg)}")
                
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
            
        finally:
            # Clean up downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)

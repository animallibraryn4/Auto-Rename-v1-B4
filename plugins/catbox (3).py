from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
from fp.fp import FreeProxy


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
                # Automatic working proxy dhoondna
                proxy_url = FreeProxy(https=True).get() 
                proxies = {"http": proxy_url, "https": proxy_url}
                
                # Upload to Catbox
                with open(file_path, "rb") as f:
                    response = requests.post(
                        "https://catbox.moe/user/api.php",
                         data={"reqtype": "fileupload"},
                         files={"fileToUpload": f},
                         timeout=20  
                    )
                
                if response.status_code == 200 and response.text.strip():
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
                    await msg.edit_text("❌ Upload failed")
                    
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
            proxy_url = FreeProxy(https=True).get()
            proxies = {"http": proxy_url, "https": proxy_url}
        except Exception:
            proxies = None  # Fallback to direct connection if no proxy found
            
            # Upload to Catbox
            with open(file_path, "rb") as f:
                response = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    proxies=proxies, # Proxy yahan add ho rahi hai
                    timeout=20      # Timeout thoda zyada rakhein
                )
            
            if response.status_code == 200 and response.text.strip():
                # Success - get the link
                catbox_url = response.text.strip()
                
                # Send success message with button
                await msg.edit_text(
                    "✅ Upload Successful",
                    reply_mup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔗 Open Link", url=catbox_url)]
                    ])
                )
            else:
                await msg.edit_text("❌ Upload failed")
                
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)}")
            
        finally:
            # Clean up downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)

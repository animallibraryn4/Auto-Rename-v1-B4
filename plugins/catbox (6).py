from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
import random
import asyncio

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
            
            await msg.edit_text("📤 Uploading to Catbox...")
            
            try:
                # METHOD 1: Try direct upload first (without proxy)
                try:
                    await msg.edit_text("📤 Uploading to Catbox... (Direct)")
                    with open(file_path, "rb") as f:
                        response = requests.post(
                            "https://catbox.moe/user/api.php",
                            data={"reqtype": "fileupload"},
                            files={"fileToUpload": f},
                            timeout=45  # Longer timeout for direct
                        )
                    
                    if response.status_code == 200 and response.text.strip():
                        catbox_url = response.text.strip()
                        await send_success_message(msg, catbox_url)
                        return
                        
                except Exception as direct_error:
                    await msg.edit_text("⚠️ Direct upload failed, trying with proxies...")
                    await asyncio.sleep(2)
                
                # METHOD 2: Try with proxies
                proxy_list = [
                    # SOCKS5 proxies
                    {"http": "socks5://104.248.63.17:30588", "https": "socks5://104.248.63.17:30588"},
                    {"http": "socks5://209.159.153.19:22866", "https": "socks5://209.159.153.19:22866"},
                    {"http": "socks5://142.93.105.156:59166", "https": "socks5://142.93.105.156:59166"},
                    # HTTP proxies
                    {"http": "http://195.158.18.236:3128", "https": "http://195.158.18.236:3128"},
                    {"http": "http://45.152.188.241:3128", "https": "http://45.152.188.241:3128"},
                    {"http": "http://46.250.171.31:3128", "https": "http://46.250.171.31:3128"},
                ]
                
                random.shuffle(proxy_list)
                
                for i, proxy in enumerate(proxy_list):
                    try:
                        await msg.edit_text(f"📤 Trying proxy {i+1}/{len(proxy_list)}...")
                        
                        with open(file_path, "rb") as f:
                            response = requests.post(
                                "https://catbox.moe/user/api.php",
                                data={"reqtype": "fileupload"},
                                files={"fileToUpload": f},
                                proxies=proxy,
                                timeout=25,
                                verify=False
                            )
                        
                        if response.status_code == 200 and response.text.strip():
                            catbox_url = response.text.strip()
                            await send_success_message(msg, catbox_url)
                            return
                            
                    except Exception:
                        continue
                
                # METHOD 3: Try alternative URLs
                alternative_urls = [
                    "https://catbox.moe/user/api.php",
                    "https://catboxmoe.com/user/api.php",  # Alternative domain
                ]
                
                for url in alternative_urls:
                    try:
                        await msg.edit_text(f"🔄 Trying alternative URL...")
                        
                        with open(file_path, "rb") as f:
                            response = requests.post(
                                url,
                                data={"reqtype": "fileupload"},
                                files={"fileToUpload": f},
                                timeout=30
                            )
                        
                        if response.status_code == 200 and response.text.strip():
                            catbox_url = response.text.strip()
                            await send_success_message(msg, catbox_url)
                            return
                            
                    except Exception:
                        continue
                
                # All methods failed
                await msg.edit_text(
                    "❌ Upload failed. Possible solutions:\n\n"
                    "1. Try again in a few minutes\n"
                    "2. Check your internet connection\n"
                    "3. The file might be too large\n"
                    "4. Catbox servers might be down"
                )
                    
            except Exception as e:
                await msg.edit_text(f"❌ Error: {str(e)[:150]}")
                
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
        
        await msg.edit_text("📤 Uploading to Catbox...")
        
        try:
            # METHOD 1: Try direct upload first
            try:
                await msg.edit_text("📤 Uploading to Catbox... (Direct)")
                with open(file_path, "rb") as f:
                    response = requests.post(
                        "https://catbox.moe/user/api.php",
                        data={"reqtype": "fileupload"},
                        files={"fileToUpload": f},
                        timeout=45
                    )
                
                if response.status_code == 200 and response.text.strip():
                    catbox_url = response.text.strip()
                    await send_success_message(msg, catbox_url)
                    return
                    
            except Exception:
                await msg.edit_text("⚠️ Direct upload failed, trying with proxies...")
                await asyncio.sleep(2)
            
            # METHOD 2: Try with proxies
            proxy_list = [
                {"http": "socks5://104.248.63.17:30588", "https": "socks5://104.248.63.17:30588"},
                {"http": "socks5://209.159.153.19:22866", "https": "socks5://209.159.153.19:22866"},
                {"http": "http://195.158.18.236:3128", "https": "http://195.158.18.236:3128"},
                {"http": "http://45.152.188.241:3128", "https": "http://45.152.188.241:3128"},
            ]
            
            random.shuffle(proxy_list)
            
            for i, proxy in enumerate(proxy_list):
                try:
                    await msg.edit_text(f"📤 Trying proxy {i+1}/{len(proxy_list)}...")
                    
                    with open(file_path, "rb") as f:
                        response = requests.post(
                            "https://catbox.moe/user/api.php",
                            data={"reqtype": "fileupload"},
                            files={"fileToUpload": f},
                            proxies=proxy,
                            timeout=25,
                            verify=False
                        )
                    
                    if response.status_code == 200 and response.text.strip():
                        catbox_url = response.text.strip()
                        await send_success_message(msg, catbox_url)
                        return
                        
                except Exception:
                    continue
            
            # All methods failed
            await msg.edit_text(
                "❌ Upload failed. Possible solutions:\n\n"
                "1. Try again in a few minutes\n"
                "2. Check your internet connection\n"
                "3. The file might be too large\n"
                "4. Catbox servers might be down"
            )
                
        except Exception as e:
            await msg.edit_text(f"❌ Error: {str(e)[:150]}")
            
        finally:
            # Clean up downloaded file
            if os.path.exists(file_path):
                os.remove(file_path)

# Helper function to send success message
async def send_success_message(msg, catbox_url):
    await msg.edit_text(
        f"✅ **Upload Successful!**\n\n"
        f"**Direct Link:** `{catbox_url}`\n\n"
        f"**Short Link:** https://catbox.moe/c/{catbox_url.split('/')[-1]}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Link", url=catbox_url)],
            [InlineKeyboardButton("📋 Copy Link", text=catbox_url)],
            [InlineKeyboardButton("🌐 Short Link", url=f"https://catbox.moe/c/{catbox_url.split('/')[-1]}")]
        ])
    )

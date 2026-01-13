from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os

@Client.on_message(filters.command("catbox") & filters.private)
async def catbox_upload(client, message):
    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.photo or reply.document:
            msg = await message.reply_text("📥 Downloading file...")
            file_path = await reply.download()
            await msg.edit_text("📤 Uploading to Catbox...")
            
            try:
                # Direct upload without unstable proxies
                with open(file_path, "rb") as f:
                    response = requests.post(
                        "https://catbox.moe/user/api.php",
                        data={"reqtype": "fileupload"},
                        files={"fileToUpload": f},
                        timeout=30
                    )
                
                if response.status_code == 200 and response.text.strip():
                    catbox_url = response.text.strip()
                    await msg.edit_text(
                        "✅ Upload Successful",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔗 Open Link", url=catbox_url)]
                        ])
                    )
                else:
                    await msg.edit_text("❌ Upload failed: Server rejected the file.")
            except Exception as e:
                await msg.edit_text(f"❌ Error: {str(e)}")
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            await message.reply_text("❌ Please reply to an image or file")
    else:
        await message.reply_text("**Usage:** Reply to a file with `/catbox`")

@Client.on_message(filters.photo & filters.private)
async def handle_photo_with_caption(client, message):
    if message.caption and "/catbox" in message.caption:
        msg = await message.reply_text("📥 Downloading file...")
        file_path = await message.download()
        await msg.edit_text("📤 Uploading to Catbox...")
        
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=30
                )
            
            if response.status_code == 200 and response.text.strip():
                catbox_url = response.text.strip()
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
            if os.path.exists(file_path):
                os.remove(file_path)

        

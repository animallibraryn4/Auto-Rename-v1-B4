from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os

# Use higher priority group to ensure our handler runs first
@Client.on_message(filters.command("catbox") & filters.private, group=0)  # group=0 is highest priority
async def catbox_upload(client, message):
    # Check if user replied to a message
    if message.reply_to_message:
        # Get the replied message
        reply = message.reply_to_message
        
        # Check if it has media (photo, document, video, etc.)
        if any([
            reply.photo,
            reply.document,
            reply.video,
            reply.animation,
            reply.sticker
        ]):
            # Download the file
            msg = await message.reply_text("📥 Downloading file...")
            
            # Download file
            file_path = await reply.download()
            
            if not os.path.exists(file_path):
                await msg.edit_text("❌ Failed to download file")
                return
            
            # Upload to Catbox
            await msg.edit_text("📤 Uploading to Catbox...")
            
            try:
                # Get filename for upload
                filename = os.path.basename(file_path)
                
                # Upload to Catbox
                with open(file_path, "rb") as f:
                    response = requests.post(
                        "https://catbox.moe/user/api.php",
                        data={"reqtype": "fileupload"},
                        files={"fileToUpload": (filename, f)}
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
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
        else:
            # Replied message has no media
            await message.reply_text("❌ Please reply to a photo, video, or file")
    else:
        # No reply - send instructions
        await message.reply_text(
            "**How to use Catbox Upload:**\n\n"
            "1. Send any photo/image to the bot\n"
            "2. Reply to that message with `/catbox`\n"
            "3. Get a direct link!\n\n"
            "✅ Supports: Photos, Videos, Documents, GIFs"
        )

# Also handle when user sends photo with caption /catbox (with priority)
@Client.on_message(filters.photo & filters.private, group=0)
async def handle_photo_with_caption(client, message):
    # Check if caption contains /catbox command
    if message.caption and "/catbox" in message.caption.lower():
        # Skip if user is in thumbnail setting mode
        from helper.database import n4bots
        user_id = message.from_user.id
        quality = await n4bots.get_temp_quality(user_id)
        
        # If user is setting a thumbnail, let quality_thumb.py handle it
        if quality:
            print(f"User {user_id} is in thumbnail mode, skipping Catbox")
            return
        
        # Download the file
        msg = await message.reply_text("📥 Downloading file...")
        
        # Download file
        file_path = await message.download()
        
        if not os.path.exists(file_path):
            await msg.edit_text("❌ Failed to download file")
            return
        
        # Upload to Catbox
        await msg.edit_text("📤 Uploading to Catbox...")
        
        try:
            # Get filename for upload
            filename = f"photo_{message.id}.jpg"
            
            # Upload to Catbox
            with open(file_path, "rb") as f:
                response = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": (filename, f)}
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
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass

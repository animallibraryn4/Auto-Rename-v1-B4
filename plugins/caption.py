from pyrogram import Client, filters 
from helper.database import n4bots
import requests
import os
from pyrogram import Client, filters

@Client.on_message(filters.private & filters.command('set_caption'))
async def add_caption(client, message):
    if len(message.command) == 1:
       return await message.reply_text("**Give The Caption\n\nExample :- `/set_caption 📕Name ➠ : {filename} \n\n🔗 Size ➠ : {filesize} \n\n⏰ Duration ➠ : {duration}`**")
    caption = message.text.split(" ", 1)[1]
    await n4bots.set_caption(message.from_user.id, caption=caption)
    await message.reply_text("**Your Caption Successfully Added ✅**")

@Client.on_message(filters.private & filters.command('del_caption'))
async def delete_caption(client, message):
    caption = await n4bots.get_caption(message.from_user.id)  
    if not caption:
       return await message.reply_text("**You Don't Have Any Caption ❌**")
    await n4bots.set_caption(message.from_user.id, caption=None)
    await message.reply_text("**Your Caption Successfully Deleted 🗑️**")

@Client.on_message(filters.private & filters.command(['see_caption', 'view_caption']))
async def see_caption(client, message):
    caption = await n4bots.get_caption(message.from_user.id)  
    if caption:
       await message.reply_text(f"**Your Caption :**\n\n`{caption}`")
    else:
       await message.reply_text("**You Don't Have Any Caption ❌**")

@Client.on_message(filters.command("catbox") & filters.reply)
async def catbox_upload(client, message):
    reply = message.reply_to_message

    if not reply.photo and not reply.document:
        await message.reply_text("Reply to an image or file.")
        return

    msg = await message.reply_text("Uploading to Catbox...")

    file_path = await reply.download()

    try:
        with open(file_path, "rb") as f:
            r = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f}
            )

        if r.status_code == 200:
            await msg.edit(f"✅ Uploaded\n\n{r.text.strip()}")
        else:
            await msg.edit("Upload failed.")

    except Exception as e:
        await msg.edit("Error while uploading.")

    if os.path.exists(file_path):
        os.remove(file_path)

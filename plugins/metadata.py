
from helper.database import n4bots as db
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import Txt

async def get_metadata_summary(user_id):
    """Generate a summary of all metadata settings"""
    current = await db.get_metadata(user_id)
    title = await db.get_title(user_id)
    author = await db.get_author(user_id)
    artist = await db.get_artist(user_id)
    video = await db.get_video(user_id)
    audio = await db.get_audio(user_id)
    subtitle = await db.get_subtitle(user_id)
    
    summary = f"""
**㊋ Mᴇᴛᴀᴅᴀᴛᴀ Sᴛᴀᴛᴜs: {current}**

**◈ Tɪᴛʟᴇ ▸** `{title if title else 'Nᴏᴛ ꜱᴇᴛ'}`
**◈ Aᴜᴛʜᴏʀ ▸** `{author if author else 'Nᴏᴛ ꜱᴇᴛ'}`
**◈ Aʀᴛɪꜱᴛ ▸** `{artist if artist else 'Nᴏᴛ ꜱᴇᴛ'}`
**◈ Aᴜᴅɪᴏ ▸** `{audio if audio else 'Nᴏᴛ ꜱᴇᴛ'}`
**◈ Sᴜʙᴛɪᴛʟᴇ ▸** `{subtitle if subtitle else 'Nᴏᴛ ꜱᴇᴛ'}`
**◈ Vɪᴅᴇᴏ ▸** `{video if video else 'Nᴏᴛ ꜱᴇᴛ'}`
"""
    return summary

def get_metadata_control_keyboard(current_status, editing_field=None):
    """Generate appropriate keyboard based on current state"""
    
    if editing_field:
        # Editing mode - show field-specific controls
        buttons = [
            [
                InlineKeyboardButton("📝 Sᴇɴᴅ Nᴇᴡ Vᴀʟᴜᴇ", callback_data=f"set_{editing_field}"),
                InlineKeyboardButton("❌ Cʟᴇᴀʀ Fɪᴇʟᴅ", callback_data=f"clear_{editing_field}")
            ],
            [
                InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="metadata_home"),
                InlineKeyboardButton("📖 Hᴇʟᴘ", callback_data="meta_info")
            ]
        ]
    else:
        # Main control panel
        buttons = [
            [
                InlineKeyboardButton(
                    f"{'✅' if current_status == 'On' else '  '} Mᴇᴛᴀᴅᴀᴛᴀ Oɴ", 
                    callback_data='on_metadata'
                ),
                InlineKeyboardButton(
                    f"{'✅' if current_status == 'Off' else '  '} Mᴇᴛᴀᴅᴀᴛᴀ Oғғ", 
                    callback_data='off_metadata'
                )
            ],
            [
                InlineKeyboardButton("📝 Tɪᴛʟᴇ", callback_data="edit_title"),
                InlineKeyboardButton("👤 Aᴜᴛʜᴏʀ", callback_data="edit_author")
            ],
            [
                InlineKeyboardButton("🎨 Aʀᴛɪꜱᴛ", callback_data="edit_artist"),
                InlineKeyboardButton("🎵 Aᴜᴅɪᴏ", callback_data="edit_audio")
            ],
            [
                InlineKeyboardButton("📺 Sᴜʙᴛɪᴛʟᴇ", callback_data="edit_subtitle"),
                InlineKeyboardButton("🎬 Vɪᴅᴇᴏ", callback_data="edit_video")
            ],
            [
                InlineKeyboardButton("🔄 Rᴇꜱᴇᴛ Aʟʟ", callback_data="reset_all"),
                InlineKeyboardButton("📖 Hᴏᴡ Tᴏ", callback_data="meta_info")
            ],
            [
                InlineKeyboardButton("❌ Cʟᴏꜱᴇ", callback_data="close_meta")
            ]
        ]
    
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("metadata"))
async def metadata_main(client, message):
    user_id = message.from_user.id
    current_status = await db.get_metadata(user_id)
    
    summary = await get_metadata_summary(user_id)
    
    text = f"""
**🎛️ Mᴇᴛᴀᴅᴀᴛᴀ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ**

*Cᴇɴᴛʀᴀʟɪᴢᴇᴅ ᴄᴏɴᴛʀᴏʟ ꜰᴏʀ ᴀʟʟ ʏᴏᴜʀ ᴍᴇᴛᴀᴅᴀᴛᴀ ɴᴇᴇᴅꜱ*

{summary}

**❐ Iɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ:**
• Tᴏɢɢʟᴇ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴏɴ/ᴏꜰꜰ ᴜꜱɪɴɢ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ
• Cʟɪᴄᴋ ᴀɴʏ ꜰɪᴇʟᴅ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴇᴅɪᴛ
• Uꜱᴇ "Hᴏᴡ Tᴏ" ꜰᴏʀ ᴅᴇᴛᴀɪʟᴇᴅ ɢᴜɪᴅᴇ
"""
    
    keyboard = get_metadata_control_keyboard(current_status)
    
    await message.reply_text(
        text=text, 
        reply_markup=keyboard, 
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^(on_metadata|off_metadata|edit_|set_|clear_|reset_all|metadata_home|meta_info|close_meta)"))
async def metadata_callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    # Handle toggle commands
    if data == "on_metadata":
        await db.set_metadata(user_id, "On")
        await query.answer("✅ Mᴇᴛᴀᴅᴀᴔᴀ ᴇɴᴀʙʟᴇᴅ")
    
    elif data == "off_metadata":
        await db.set_metadata(user_id, "Off")
        await query.answer("❌ Mᴇᴛᴀᴅᴀᴔᴀ ᴅɪꜱᴀʙʟᴇᴅ")
    
    # Handle edit field selection
    elif data.startswith("edit_"):
        field = data.split("_")[1]
        field_display = field.capitalize()
        
        # Get current value
        if field == "title":
            current_value = await db.get_title(user_id)
        elif field == "author":
            current_value = await db.get_author(user_id)
        elif field == "artist":
            current_value = await db.get_artist(user_id)
        elif field == "audio":
            current_value = await db.get_audio(user_id)
        elif field == "subtitle":
            current_value = await db.get_subtitle(user_id)
        elif field == "video":
            current_value = await db.get_video(user_id)
        else:
            current_value = "Not set"
        
        text = f"""
**✏️ Eᴅɪᴛ {field_display}**

**Cᴜʀʀᴇɴᴛ Vᴀʟᴜᴇ:** `{current_value}`

**❐ Iɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ:**
• Cʟɪᴄᴋ "Sᴇɴᴅ Nᴇᴡ Vᴀʟᴜᴇ" ᴛᴏ ᴇɴᴛᴇʀ ᴀ ɴᴇᴡ ᴠᴀʟᴜᴇ
• Cʟɪᴄᴋ "Cʟᴇᴀʀ Fɪᴇʟᴅ" ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴄᴜʀʀᴇɴᴛ ᴠᴀʟᴜᴇ
• Uꜱᴇ /metadata ᴀɢᴀɪɴ ᴛᴏ ɢᴏ ʙᴀᴄᴋ
"""
        
        keyboard = get_metadata_control_keyboard(
            await db.get_metadata(user_id), 
            editing_field=field
        )
        
        await query.message.edit_text(text=text, reply_markup=keyboard)
        return
    
    # Handle setting new value
    elif data.startswith("set_"):
        field = data.split("_")[1]
        field_display = field.capitalize()
        
        await query.message.delete()
        await query.message.reply_text(
            f"**📝 Sᴇɴᴅ ᴍᴇ ᴛʜᴇ ɴᴇᴡ {field_display} ᴠᴀʟᴜᴇ:**\n\n"
            f"ᴇ.ɢ. `ᴇɴᴄᴏᴅᴇᴅ ʙʏ @ᴀɴɪᴍᴇʟɪʙʀᴀʀʏɴ4`\n\n"
            f"ᴏʀ ᴛʏᴘᴇ /cancel ᴛᴏ ᴀʙᴏʀᴛ."
        )
        
        # Store which field we're setting
        await db.col.update_one(
            {"_id": int(user_id)},
            {"$set": {"editing_metadata_field": field}}
        )
        return
    
    # Handle clearing field
    elif data.startswith("clear_"):
        field = data.split("_")[1]
        field_display = field.capitalize()
        
        # Reset to default value
        if field == "title":
            await db.set_title(user_id, "Encoded by @Animelibraryn4")
        elif field == "author":
            await db.set_author(user_id, "@Animelibraryn4")
        elif field == "artist":
            await db.set_artist(user_id, "@Animelibraryn4")
        elif field == "audio":
            await db.set_audio(user_id, "By @Animelibraryn4")
        elif field == "subtitle":
            await db.set_subtitle(user_id, "By @Animelibraryn4")
        elif field == "video":
            await db.set_video(user_id, "Encoded By @Animelibraryn4")
        
        await query.answer(f"✅ {field_display} ᴄʟᴇᴀʀᴇᴅ")
    
    # Handle reset all
    elif data == "reset_all":
        # Reset all fields to defaults
        await db.set_title(user_id, "Encoded by @Animelibraryn4")
        await db.set_author(user_id, "@Animelibraryn4")
        await db.set_artist(user_id, "@Animelibraryn4")
        await db.set_audio(user_id, "By @Animelibraryn4")
        await db.set_subtitle(user_id, "By @Animelibraryn4")
        await db.set_video(user_id, "Encoded By @Animelibraryn4")
        await query.answer("✅ Aʟʟ ᴍᴇᴛᴀᴅᴀᴛᴀ ʀᴇꜱᴇᴛ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛꜱ")
    
    # Handle back to home
    elif data == "metadata_home":
        current_status = await db.get_metadata(user_id)
        summary = await get_metadata_summary(user_id)
        
        text = f"""
**🎛️ Mᴇᴛᴀᴅᴀᴛᴀ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ**

{summary}

**❐ Iɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ:**
• Tᴏɢɢʟᴇ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴏɴ/ᴏꜰꜰ ᴜꜱɪɴɢ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ
• Cʟɪᴄᴋ ᴀɴʏ ꜰɪᴇʟᴅ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴇᴅɪᴛ
• Uꜱᴇ "Hᴏᴡ Tᴏ" ꜰᴏʀ ᴅᴇᴛᴀɪʟᴇᴅ ɢᴜɪᴅᴇ
"""
        keyboard = get_metadata_control_keyboard(current_status)
        await query.message.edit_text(text=text, reply_markup=keyboard)
        return
    
    # Handle meta info/help
    elif data == "meta_info":
        await query.message.edit_text(
            text=Txt.META_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("⬅️ Bᴀᴄᴋ", callback_data="metadata_home"),
                    InlineKeyboardButton("❌ Cʟᴏꜱᴇ", callback_data="close_meta")
                ]
            ])
        )
        return
    
    # Handle close
    elif data == "close_meta":
        await query.message.delete()
        return
    
    # Update the display after any change
    current_status = await db.get_metadata(user_id)
    summary = await get_metadata_summary(user_id)
    
    text = f"""
**🎛️ Mᴇᴛᴀᴅᴀᴛᴀ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ**

{summary}

**❐ Iɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ:**
• Tᴏɢɢʟᴇ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴏɴ/ᴏꜰꜰ ᴜꜱɪɴɢ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ
• Cʟɪᴄᴋ ᴀɴʏ ꜰɪᴇʟᴅ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴇᴅɪᴛ
• Uꜱᴇ "Hᴏᴡ Tᴏ" ꜰᴏʀ ᴅᴇᴛᴀɪʟᴇᴅ ɢᴜɪᴅᴇ
"""
    
    keyboard = get_metadata_control_keyboard(current_status)
    await query.message.edit_text(text=text, reply_markup=keyboard)

@Client.on_message(filters.private & ~filters.command("start") & ~filters.command("help") & ~filters.command("cancel"))
async def handle_metadata_value_input(client, message):
    """Handle text input for metadata fields"""
    user_id = message.from_user.id
    
    # Check if user is in metadata editing mode
    user_data = await db.col.find_one({"_id": int(user_id)})
    if not user_data or "editing_metadata_field" not in user_data:
        return
    
    field = user_data["editing_metadata_field"]
    new_value = message.text.strip()
    
    if not new_value:
        await message.reply_text("❌ Vᴀʟᴜᴇ ᴄᴀɴɴᴏᴛ ʙᴇ ᴇᴍᴘᴛʏ. Tʀʏ ᴀɢᴀɪɴ.")
        return
    
    # Update the specific field
    if field == "title":
        await db.set_title(user_id, new_value)
        field_display = "Title"
    elif field == "author":
        await db.set_author(user_id, new_value)
        field_display = "Author"
    elif field == "artist":
        await db.set_artist(user_id, new_value)
        field_display = "Artist"
    elif field == "audio":
        await db.set_audio(user_id, new_value)
        field_display = "Audio"
    elif field == "subtitle":
        await db.set_subtitle(user_id, new_value)
        field_display = "Subtitle"
    elif field == "video":
        await db.set_video(user_id, new_value)
        field_display = "Video"
    else:
        await message.reply_text("❌ Iɴᴠᴀʟɪᴅ ꜰɪᴇʟᴅ.")
        return
    
    # Clear editing flag
    await db.col.update_one(
        {"_id": int(user_id)},
        {"$unset": {"editing_metadata_field": ""}}
    )
    
    # Show updated panel
    current_status = await db.get_metadata(user_id)
    summary = await get_metadata_summary(user_id)
    
    text = f"""
**🎛️ Mᴇᴛᴀᴅᴀᴛᴀ Cᴏɴᴛʀᴏʟ Pᴀɴᴇʟ**

**✅ {field_display} ᴜᴘᴅᴀᴛᴇᴅ ᴛᴏ:** `{new_value}`

{summary}

**❐ Iɴꜱᴛʀᴜᴄᴛɪᴏɴꜱ:**
• Tᴏɢɢʟᴇ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴏɴ/ᴏꜰꜰ ᴜꜱɪɴɢ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ
• Cʟɪᴄᴋ ᴀɴʏ ꜰɪᴇʟᴅ ʙᴜᴛᴛᴏɴ ᴛᴏ ᴇᴅɪᴛ
• Uꜱᴇ "Hᴏᴡ Tᴏ" ꜰᴏʀ ᴅᴇᴛᴀɪʟᴇᴅ ɢᴜɪᴅᴇ
"""
    
    keyboard = get_metadata_control_keyboard(current_status)
    await message.reply_text(text=text, reply_markup=keyboard)

@Client.on_message(filters.command("cancel"))
async def cancel_metadata_edit(client, message):
    """Cancel metadata editing"""
    user_id = message.from_user.id
    
    # Check if user is in editing mode
    user_data = await db.col.find_one({"_id": int(user_id)})
    if user_data and "editing_metadata_field" in user_data:
        await db.col.update_one(
            {"_id": int(user_id)},
            {"$unset": {"editing_metadata_field": ""}}
        )
        await message.reply_text("❌ Mᴇᴛᴀᴅᴀᴛᴀ ᴇᴅɪᴛɪɴɢ ᴄᴀɴᴄᴇʟʟᴇᴅ.")
        
        # Show main panel
        await metadata_main(client, message)
    else:
        await message.reply_text("⚠️ Nᴏ ᴀᴄᴛɪᴠᴇ ᴇᴅɪᴛɪɴɢ ᴛᴏ ᴄᴀɴᴄᴇʟ.")

# Remove all individual set commands - now handled by /metadata only
# No separate /settitle, /setauthor, etc. commands needed

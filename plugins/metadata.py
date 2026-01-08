from helper.database import n4bots as db
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import Txt

@Client.on_message(filters.command("metadata"))
async def metadata_main(client, message):
    """Main metadata management command with dynamic settings"""
    user_id = message.from_user.id
    
    # Get current metadata status and values
    current_status = await db.get_metadata(user_id)
    metadata_values = {
        "title": await db.get_title(user_id),
        "author": await db.get_author(user_id),
        "artist": await db.get_artist(user_id),
        "video": await db.get_video(user_id),
        "audio": await db.get_audio(user_id),
        "subtitle": await db.get_subtitle(user_id)
    }
    
    # Display current settings
    text = f"""
**🛠️ Metadata Management System**

**⚙️ Current Status:** `{"✅ ON" if current_status == "On" else "❌ OFF"}`

**Current Metadata Values:**

**Instructions:**
1. First, toggle metadata ON/OFF
2. Then click "Edit Metadata" to modify all values at once
3. Enter new values separated by new lines
"""
    
    # Main buttons
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"✅ ON" if current_status == "On" else "ON", 
                callback_data='on_metadata'
            ),
            InlineKeyboardButton(
                f"❌ OFF" if current_status == "Off" else "OFF", 
                callback_data='off_metadata'
            )
        ],
        [InlineKeyboardButton("✏️ Edit Metadata", callback_data="edit_metadata")],
        [InlineKeyboardButton("📖 Help", callback_data="meta_help")]
    ])
    
    await message.reply_text(text=text, reply_markup=buttons, disable_web_page_preview=True)

@Client.on_callback_query(filters.regex(r"on_metadata|off_metadata|edit_metadata|meta_help|save_metadata|cancel_edit"))
async def metadata_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    if data == "on_metadata":
        await db.set_metadata(user_id, "On")
        await query.answer("✅ Metadata turned ON", show_alert=True)
        
    elif data == "off_metadata":
        await db.set_metadata(user_id, "Off")
        await query.answer("❌ Metadata turned OFF", show_alert=True)
    
    elif data == "edit_metadata":
        # Get current values
        current_values = {
            "title": await db.get_title(user_id),
            "author": await db.get_author(user_id),
            "artist": await db.get_artist(user_id),
            "audio": await db.get_audio(user_id),
            "subtitle": await db.get_subtitle(user_id),
            "video": await db.get_video(user_id)
        }
        
        # Create editing guide
        edit_text = f"""
**✏️ Edit All Metadata Values**

**Format (enter each on a new line):**

**Current Values:**
• **title:** `{current_values['title']}`
• **author:** `{current_values['author']}`
• **artist:** `{current_values['artist']}`
• **audio:** `{current_values['audio']}`
• **subtitle:** `{current_values['subtitle']}`
• **video:** `{current_values['video']}`

**Reply to this message with your new metadata in the format above.**
"""
        
        # Store that user is in edit mode
        await db.col.update_one(
            {"_id": user_id},
            {"$set": {"editing_metadata": True}},
            upsert=True
        )
        
        await query.message.edit_text(
            text=edit_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_edit")]
            ])
        )
        return
    
    elif data == "cancel_edit":
        # Remove edit mode
        await db.col.update_one(
            {"_id": user_id},
            {"$unset": {"editing_metadata": ""}}
        )
        await query.message.edit_text("✏️ Metadata editing cancelled.")
        return
    
    elif data == "meta_help":
        await query.message.edit_text(
            text=Txt.META_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_metadata")]
            ])
        )
        return
    
    elif data == "back_to_metadata":
        # Refresh the metadata management screen
        await metadata_main(client, query.message)
        return
    
    # Refresh the main metadata screen
    await metadata_main(client, query.message)

@Client.on_message(filters.private & filters.text & ~filters.command)
async def handle_metadata_input(client, message):
    """Handle metadata input when user is in edit mode"""
    user_id = message.from_user.id
    
    # Check if user is in metadata edit mode
    user_data = await db.col.find_one({"_id": user_id})
    if not user_data or not user_data.get("editing_metadata"):
        return
    
    # Parse the metadata input
    metadata_lines = message.text.strip().split('\n')
    metadata_dict = {}
    
    for line in metadata_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key in ['title', 'author', 'artist', 'audio', 'subtitle', 'video']:
                metadata_dict[key] = value
    
    # Update database with new values
    if metadata_dict:
        updates = {}
        if 'title' in metadata_dict:
            updates['title'] = metadata_dict['title']
            await db.set_title(user_id, metadata_dict['title'])
        
        if 'author' in metadata_dict:
            updates['author'] = metadata_dict['author']
            await db.set_author(user_id, metadata_dict['author'])
        
        if 'artist' in metadata_dict:
            updates['artist'] = metadata_dict['artist']
            await db.set_artist(user_id, metadata_dict['artist'])
        
        if 'audio' in metadata_dict:
            updates['audio'] = metadata_dict['audio']
            await db.set_audio(user_id, metadata_dict['audio'])
        
        if 'subtitle' in metadata_dict:
            updates['subtitle'] = metadata_dict['subtitle']
            await db.set_subtitle(user_id, metadata_dict['subtitle'])
        
        if 'video' in metadata_dict:
            updates['video'] = metadata_dict['video']
            await db.set_video(user_id, metadata_dict['video'])
        
        # Clear edit mode
        await db.col.update_one(
            {"_id": user_id},
            {"$unset": {"editing_metadata": ""}}
        )
        
        # Show confirmation
        confirmation_text = "✅ **Metadata Updated Successfully!**\n\n"
        for key, value in updates.items():
            confirmation_text += f"**{key.title()}:** `{value}`\n"
        
        await message.reply_text(
            confirmation_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Manage Metadata", callback_data="back_to_metadata")]
            ])
        )
    else:
        await message.reply_text(
            "❌ **Invalid format!**\n\n"
            "Please use the format:\n"
            "```\n"
            "title: Your Title\n"
            "author: Author Name\n"
            "artist: Artist Name\n"
            "audio: Audio Track\n"
            "subtitle: Subtitle\n"
            "video: Video Track\n"
            "```",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_edit")]
            ])
        )

# Remove individual command handlers - these are now handled by the dynamic system
# Note: The old handlers are removed from this file

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
**📊 Metadata Status: {current}**

**┌ Title:** `{title if title else 'Not Set'}`
**├ Author:** `{author if author else 'Not Set'}`
**├ Artist:** `{artist if artist else 'Not Set'}`
**├ Audio:** `{audio if audio else 'Not Set'}`
**├ Subtitle:** `{subtitle if subtitle else 'Not Set'}`
**└ Video:** `{video if video else 'Not Set'}`
"""
    return summary

def get_metadata_control_keyboard(current_status, editing_field=None):
    """Generate appropriate keyboard based on current state"""
    
    if editing_field:
        # Editing mode - show field-specific controls
        buttons = [
            [
                InlineKeyboardButton("✏️ Set New Value", callback_data=f"set_{editing_field}"),
                InlineKeyboardButton("🗑️ Clear Field", callback_data=f"clear_{editing_field}")
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="metadata_home"),
                InlineKeyboardButton("❓ Help", callback_data="meta_info")
            ]
        ]
    else:
        # Main control panel
        buttons = [
            [
                InlineKeyboardButton(
                    f"{'✅' if current_status == 'On' else '○'} Enable", 
                    callback_data='on_metadata'
                ),
                InlineKeyboardButton(
                    f"{'✅' if current_status == 'Off' else '○'} Disable", 
                    callback_data='off_metadata'
                )
            ],
            [
                InlineKeyboardButton("⚙️ Set Metadata", callback_data="set_metadata_menu")
            ],
            [
                InlineKeyboardButton("📝 Edit Title", callback_data="edit_title"),
                InlineKeyboardButton("👤 Edit Author", callback_data="edit_author")
            ],
            [
                InlineKeyboardButton("🎨 Edit Artist", callback_data="edit_artist"),
                InlineKeyboardButton("🎵 Edit Audio", callback_data="edit_audio")
            ],
            [
                InlineKeyboardButton("📺 Edit Subtitle", callback_data="edit_subtitle"),
                InlineKeyboardButton("🎬 Edit Video", callback_data="edit_video")
            ],
            [
                InlineKeyboardButton("🔄 Reset All", callback_data="reset_all"),
                InlineKeyboardButton("❓ Help", callback_data="meta_info")
            ],
            [
                InlineKeyboardButton("✖️ Close", callback_data="close_meta")
            ]
        ]
    
    return InlineKeyboardMarkup(buttons)

def get_set_metadata_keyboard():
    """Keyboard for setting metadata values"""
    buttons = [
        [
            InlineKeyboardButton("📝 Set Title", callback_data="set_title"),
            InlineKeyboardButton("👤 Set Author", callback_data="set_author")
        ],
        [
            InlineKeyboardButton("🎨 Set Artist", callback_data="set_artist"),
            InlineKeyboardButton("🎵 Set Audio", callback_data="set_audio")
        ],
        [
            InlineKeyboardButton("📺 Set Subtitle", callback_data="set_subtitle"),
            InlineKeyboardButton("🎬 Set Video", callback_data="set_video")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="metadata_home"),
            InlineKeyboardButton("✖️ Close", callback_data="close_meta")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("metadata"))
async def metadata_main(client, message):
    user_id = message.from_user.id
    current_status = await db.get_metadata(user_id)
    
    summary = await get_metadata_summary(user_id)
    
    text = f"""
**✨ Metadata Control Panel**

*Customize how your media files appear with metadata settings*

{summary}

**📌 Instructions:**
• Toggle metadata On/Off to enable or disable all metadata
• Use "Set Metadata" to configure individual fields
• Click on specific fields to edit them directly
• Use "Help" for detailed information about metadata
"""
    
    keyboard = get_metadata_control_keyboard(current_status)
    
    await message.reply_text(
        text=text, 
        reply_markup=keyboard, 
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^(on_metadata|off_metadata|edit_|set_|clear_|reset_all|metadata_home|meta_info|close_meta|set_metadata_menu)"))
async def metadata_callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    # Handle toggle commands
    if data == "on_metadata":
        await db.set_metadata(user_id, "On")
        await query.answer("✅ Metadata enabled")
    
    elif data == "off_metadata":
        await db.set_metadata(user_id, "Off")
        await query.answer("❌ Metadata disabled")
    
    # Handle "Set Metadata" menu
    elif data == "set_metadata_menu":
        text = """
**⚙️ Set Metadata Values**

Choose which metadata field you want to set:

**📝 Title** - The main title of the media
**👤 Author** - The creator or uploader
**🎨 Artist** - The artist/performer
**🎵 Audio** - Audio track information
**📺 Subtitle** - Subtitle track information
**🎬 Video** - Video quality/encoding info

Click on any field to set a new value.
"""
        keyboard = get_set_metadata_keyboard()
        await query.message.edit_text(text=text, reply_markup=keyboard)
        return
    
    # Handle edit field selection
    elif data.startswith("edit_"):
        field = data.split("_")[1]
        await show_edit_field(query, user_id, field)
        return
    
    # Handle set field directly from menu
    elif data.startswith("set_") and data != "set_metadata_menu":
        field = data.split("_")[1]
        
        await query.message.delete()
        await query.message.reply_text(
            f"**✏️ Send me the new {field.capitalize()} value:**\n\n"
            f"**Example:** `{get_field_example(field)}`\n\n"
            f"Type /cancel to cancel this operation."
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
        default_values = {
            "title": "Encoded by @Animelibraryn4",
            "author": "@Animelibraryn4",
            "artist": "@Animelibraryn4",
            "audio": "By @Animelibraryn4",
            "subtitle": "By @Animelibraryn4",
            "video": "Encoded By @Animelibraryn4"
        }
        
        if field in default_values:
            method_name = f"set_{field}"
            method = getattr(db, method_name, None)
            if method:
                await method(user_id, default_values[field])
                await query.answer(f"✅ {field_display} cleared to default")
    
    # Handle reset all
    elif data == "reset_all":
        # Reset all fields to defaults
        await db.set_title(user_id, "Encoded by @Animelibraryn4")
        await db.set_author(user_id, "@Animelibraryn4")
        await db.set_artist(user_id, "@Animelibraryn4")
        await db.set_audio(user_id, "By @Animelibraryn4")
        await db.set_subtitle(user_id, "By @Animelibraryn4")
        await db.set_video(user_id, "Encoded By @Animelibraryn4")
        await query.answer("✅ All metadata reset to default values")
    
    # Handle back to home
    elif data == "metadata_home":
        await show_main_panel(query, user_id)
        return
    
    # Handle meta info/help
    elif data == "meta_info":
        await query.message.edit_text(
            text=Txt.META_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔙 Back", callback_data="metadata_home"),
                    InlineKeyboardButton("✖️ Close", callback_data="close_meta")
                ]
            ])
        )
        return
    
    # Handle close
    elif data == "close_meta":
        await query.message.delete()
        return
    
    # Update the display after any change
    await show_main_panel(query, user_id)

def get_field_example(field):
    """Get example value for a field"""
    examples = {
        "title": "My Awesome Video",
        "author": "Your Name",
        "artist": "Artist Name",
        "audio": "High Quality Audio",
        "subtitle": "English Subtitles",
        "video": "HD 1080p"
    }
    return examples.get(field, "Your custom value")

async def show_edit_field(query, user_id, field):
    """Show edit interface for a specific field"""
    field_display = field.capitalize()
    
    # Get current value
    method_name = f"get_{field}"
    method = getattr(db, method_name, None)
    current_value = await method(user_id) if method else "Not set"
    
    text = f"""
**🔧 Edit {field_display}**

**Current Value:** `{current_value}`

**📝 Options:**
• Click **Set New Value** to change this field
• Click **Clear Field** to reset to default
• Go **Back** to return to main panel
"""
    
    keyboard = get_metadata_control_keyboard(
        await db.get_metadata(user_id), 
        editing_field=field
    )
    
    await query.message.edit_text(text=text, reply_markup=keyboard)

async def show_main_panel(query, user_id):
    """Show the main metadata panel"""
    current_status = await db.get_metadata(user_id)
    summary = await get_metadata_summary(user_id)
    
    text = f"""
**✨ Metadata Control Panel**

{summary}

**📌 Quick Actions:**
• **Enable/Disable** - Toggle metadata on or off
• **Set Metadata** - Configure all fields at once
• **Edit Fields** - Modify individual metadata values
• **Reset All** - Restore default settings
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
        await message.reply_text("❌ Empty value not allowed. Please try again.")
        return
    
    # Update the specific field
    field_methods = {
        "title": db.set_title,
        "author": db.set_author,
        "artist": db.set_artist,
        "audio": db.set_audio,
        "subtitle": db.set_subtitle,
        "video": db.set_video
    }
    
    if field in field_methods:
        await field_methods[field](user_id, new_value)
        field_display = field.capitalize()
        
        # Clear editing flag
        await db.col.update_one(
            {"_id": int(user_id)},
            {"$unset": {"editing_metadata_field": ""}}
        )
        
        # Show success message
        success_text = f"""
**✅ {field_display} Updated Successfully**

**New Value:** `{new_value}`

Your metadata has been updated. Use /metadata to see all settings.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 View Settings", callback_data="metadata_home")],
            [InlineKeyboardButton("✖️ Close", callback_data="close_meta")]
        ])
        
        await message.reply_text(text=success_text, reply_markup=keyboard)
    else:
        await message.reply_text("❌ Invalid field. Please try again.")

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
        await message.reply_text("❌ Metadata editing cancelled.")
        
        # Show main panel
        await metadata_main(client, message)
    else:
        await message.reply_text("ℹ️ No metadata editing in progress.")

import asyncio
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

def get_metadata_control_keyboard(current_status):
    """Generate main metadata control keyboard"""
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
            InlineKeyboardButton("❓ Help", callback_data="meta_info"),
            InlineKeyboardButton("✖️ Close", callback_data="close_meta")
        ]
    ]
    
    return InlineKeyboardMarkup(buttons)

def get_set_metadata_keyboard():
    """Keyboard for setting metadata values"""
    buttons = [
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
            InlineKeyboardButton("🔙 Back", callback_data="metadata_home")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_field_edit_keyboard(field):
    """Keyboard when editing a specific field"""
    buttons = [
        [
            InlineKeyboardButton("✏️ Set New Value", callback_data=f"enter_{field}"),
            InlineKeyboardButton("🗑️ Clear Field", callback_data=f"clear_{field}")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="set_metadata_menu"),
            InlineKeyboardButton("✖️ Cancel", callback_data="cancel_edit")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_input_cancel_keyboard():
    """Keyboard when user is entering text input"""
    buttons = [
        [
            InlineKeyboardButton("✖️ Cancel", callback_data="cancel_input"),
            InlineKeyboardButton("🔙 Back", callback_data="go_back_input")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

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

def get_field_display_name(field):
    """Get display name for a field"""
    names = {
        "title": "Title",
        "author": "Author",
        "artist": "Artist",
        "audio": "Audio",
        "subtitle": "Subtitle",
        "video": "Video"
    }
    return names.get(field, field.capitalize())

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
• Toggle **Enable/Disable** to control metadata
• Tap **Set Metadata** to configure individual fields
• Use **Help** for detailed information about metadata
"""
    
    keyboard = get_metadata_control_keyboard(current_status)
    
    msg = await message.reply_text(
        text=text, 
        reply_markup=keyboard, 
        disable_web_page_preview=True
    )
    
    # Store message ID for potential deletion
    await db.col.update_one(
        {"_id": int(user_id)},
        {"$set": {"last_metadata_msg_id": msg.id}}
    )

@Client.on_callback_query(filters.regex(r"^(on_metadata|off_metadata|edit_|enter_|clear_|reset_all|metadata_home|set_metadata_menu|meta_info|close_meta|cancel_edit|cancel_input|go_back_input)"))
async def metadata_callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    # Handle toggle commands
    if data == "on_metadata":
        await db.set_metadata(user_id, "On")
        # No notification shown
        await show_main_panel(query, user_id)
        return
    
    elif data == "off_metadata":
        await db.set_metadata(user_id, "Off")
        # No notification shown
        await show_main_panel(query, user_id)
        return
    
    # Handle "Set Metadata" menu
    elif data == "set_metadata_menu":
        text = """
**⚙️ Set Metadata Values**

Choose which metadata field you want to edit:

**📝 Title** - The main title of the media
**👤 Author** - The creator or uploader
**🎨 Artist** - The artist/performer
**🎵 Audio** - Audio track information
**📺 Subtitle** - Subtitle track information
**🎬 Video** - Video quality/encoding info

Click on any field to edit its value.
"""
        keyboard = get_set_metadata_keyboard()
        await query.message.edit_text(text=text, reply_markup=keyboard)
        return
    
    # Handle edit field selection
    elif data.startswith("edit_"):
        field = data.split("_")[1]
        await show_edit_field(query, user_id, field)
        return
    
    # Handle enter field value (start text input)
    elif data.startswith("enter_"):
        field = data.split("_")[1]
        field_display = get_field_display_name(field)
        
        # Get current value
        method_name = f"get_{field}"
        method = getattr(db, method_name, None)
        current_value = await method(user_id) if method else "Not set"
        
        text = f"""
**✏️ Send me the new {field_display} value:**

**Current {field_display.lower()}:** `{current_value}`

**Example:** `{get_field_example(field)}`

Please send your new value as a text message.
"""
        
        keyboard = get_input_cancel_keyboard()
        
        # Store which field we're editing
        await db.col.update_one(
            {"_id": int(user_id)},
            {"$set": {"editing_metadata_field": field}}
        )
        
        await query.message.edit_text(text=text, reply_markup=keyboard)
        return
    
    # Handle clearing field
    elif data.startswith("clear_"):
        field = data.split("_")[1]
        field_display = get_field_display_name(field)
        
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
                # No notification shown
                await show_edit_field(query, user_id, field)
        return
    
    # Handle reset all
    elif data == "reset_all":
        # Reset all fields to defaults
        await db.set_title(user_id, "Encoded by @Animelibraryn4")
        await db.set_author(user_id, "@Animelibraryn4")
        await db.set_artist(user_id, "@Animelibraryn4")
        await db.set_audio(user_id, "By @Animelibraryn4")
        await db.set_subtitle(user_id, "By @Animelibraryn4")
        await db.set_video(user_id, "Encoded By @Animelibraryn4")
        # No notification shown
        await show_set_metadata_menu(query)
        return
    
    # Handle cancel edit (from field edit screen)
    elif data == "cancel_edit":
        await show_set_metadata_menu(query)
        return
    
    # Handle cancel input (from text input screen) - DELETE WITH ANIMATION
    elif data == "cancel_input":
        # Clear editing flag
        await db.col.update_one(
            {"_id": int(user_id)},
            {"$unset": {"editing_metadata_field": ""}}
        )
        # Delete with animation
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")
        return
    
    # Handle go back from input screen
    elif data == "go_back_input":
        # Get the field we were editing
        user_data = await db.col.find_one({"_id": int(user_id)})
        if user_data and "editing_metadata_field" in user_data:
            field = user_data["editing_metadata_field"]
            # Clear editing flag
            await db.col.update_one(
                {"_id": int(user_id)},
                {"$unset": {"editing_metadata_field": ""}}
            )
            await show_edit_field(query, user_id, field)
        return
    
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
    
    # Handle close - DELETE WITH ANIMATION
    elif data == "close_meta":
        # Delete with animation
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Error deleting message: {e}")
        return

async def show_edit_field(query, user_id, field):
    """Show edit interface for a specific field"""
    field_display = get_field_display_name(field)
    
    # Get current value
    method_name = f"get_{field}"
    method = getattr(db, method_name, None)
    current_value = await method(user_id) if method else "Not set"
    
    text = f"""
**🔧 Edit {field_display}**

**Current Value:** `{current_value}`

**📝 Options:**
• **Set New Value** - Enter a new value for this field
• **Clear Field** - Reset to default value
• **Back** - Return to metadata menu
• **Cancel** - Cancel editing
"""
    
    keyboard = get_field_edit_keyboard(field)
    
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
• **Set Metadata** - Configure individual fields
• **Help** - Learn more about metadata
"""
    
    keyboard = get_metadata_control_keyboard(current_status)
    await query.message.edit_text(text=text, reply_markup=keyboard)

async def show_set_metadata_menu(query):
    """Show the set metadata menu"""
    text = """
**⚙️ Set Metadata Values**

Choose which metadata field you want to edit:

**📝 Title** - The main title of the media
**👤 Author** - The creator or uploader
**🎨 Artist** - The artist/performer
**🎵 Audio** - Audio track information
**📺 Subtitle** - Subtitle track information
**🎬 Video** - Video quality/encoding info

Click on any field to edit its value.
"""
    keyboard = get_set_metadata_keyboard()
    await query.message.edit_text(text=text, reply_markup=keyboard)

@Client.on_message(filters.private & ~filters.command(["start", "help", "metadata", "cancel"]))
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
        # Send temporary error message that will be auto-deleted
        error_msg = await message.reply_text(
            "❌ Empty value not allowed. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="go_back_input")]
            ])
        )
        
        # Delete the error message after 3 seconds
        await asyncio.sleep(3)
        try:
            await error_msg.delete()
        except:
            pass
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
        field_display = get_field_display_name(field)
        
        # Clear editing flag
        await db.col.update_one(
            {"_id": int(user_id)},
            {"$unset": {"editing_metadata_field": ""}}
        )
        
        # Show success message
        success_text = f"""
**✅ {field_display} Updated Successfully**

**New Value:** `{new_value}`

Your metadata has been updated.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Edit More", callback_data="set_metadata_menu")],
            [InlineKeyboardButton("📊 View All", callback_data="metadata_home")],
            [InlineKeyboardButton("✖️ Close", callback_data="close_meta")]
        ])
        
        await message.reply_text(text=success_text, reply_markup=keyboard)
        
        # Delete the input message with animation
        try:
            await message.delete()
        except:
            pass
    else:
        # Send temporary error message
        error_msg = await message.reply_text("❌ Invalid field. Please try again.")
        
        # Delete the error message after 3 seconds
        await asyncio.sleep(3)
        try:
            await error_msg.delete()
        except:
            pass



from helper.database import n4bots as db
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import Txt

# At the top of metadata.py, define excluded commands
EXCLUDED_COMMANDS = [
    "start", "help", "metadata", "verify", "get_token", 
    "autorename", "setmedia", "info", "set_caption", 
    "del_caption", "see_caption", "view_caption", 
    "restart", "tutorial", "stats", "status", 
    "broadcast", "donate", "bought", "sequence", 
    "sf", "fileseq", "ls", "plan", "smart_thumb", 
    "mode", "caption", "meta", "file_names", 
    "thumbnail", "metadatax", "source", "premiumx", 
    "plans", "about", "home"
]

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
**Your Metadata Is Currently: {current}**

  **Title:** `{title if title else 'Not Set'}`
  **Author:** `{author if author else 'Not Set'}`
  **Artist:** `{artist if artist else 'Not Set'}`
  **Audio:** `{audio if audio else 'Not Set'}`
  **Subtitle:** `{subtitle if subtitle else 'Not Set'}`
  **Video:** `{video if video else 'Not Set'}`
"""
    return summary

def get_main_menu_keyboard(current_status):
    """Generate main menu keyboard"""
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
            InlineKeyboardButton("🧑🏻‍💻 Set Metadata", callback_data="set_metadata_menu")
        ],
        [
            InlineKeyboardButton("Close", callback_data="close_meta")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_set_metadata_keyboard():
    """Keyboard for setting metadata values"""
    buttons = [
        [
            InlineKeyboardButton("Title", callback_data="edit_title"),
            InlineKeyboardButton("Author", callback_data="edit_author")
        ],
        [
            InlineKeyboardButton("Artist", callback_data="edit_artist"),
            InlineKeyboardButton("Audio", callback_data="edit_audio")
        ],
        [
            InlineKeyboardButton("Subtitle", callback_data="edit_subtitle"),
            InlineKeyboardButton("Video", callback_data="edit_video")
        ],
        [
            InlineKeyboardButton("Reset All", callback_data="reset_all"),
            InlineKeyboardButton("Help", callback_data="meta_info")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="metadata_home")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_edit_field_keyboard(field):
    """Keyboard for editing a specific field"""
    buttons = [
        [
            InlineKeyboardButton("Cancel", callback_data=f"cancel_edit_{field}"),
            InlineKeyboardButton("🔙 Back", callback_data="set_metadata_menu")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("metadata"))
async def metadata_main(client, message):
    user_id = message.from_user.id
    current_status = await db.get_metadata(user_id)
    
    summary = await get_metadata_summary(user_id)
    
    text = f"""
**Metadata Settings**

ᴛʜɪꜱ ʟᴇᴛꜱ ʏᴏᴜ ᴄʜᴀɴɢᴇ ᴛʜᴇ ɴᴀᴍᴇꜱ ᴀɴᴅ ᴅᴇᴛᴀɪʟꜱ ꜱʜᴏᴡɴ ᴏɴ ʏᴏᴜʀ ᴍᴇᴅɪᴀ ꜰɪʟᴇꜱ.

ʏᴏᴜ ᴄᴀɴ ᴇᴅɪᴛ ᴛʜɪɴɢꜱ ʟɪᴋᴇ ᴛɪᴛʟᴇ, ᴀᴜᴅɪᴏ ɴᴀᴍᴇ, ꜱᴜʙᴛɪᴛʟᴇ ɴᴀᴍᴇ, ᴀɴᴅ ᴀᴜᴛʜᴏʀ ꜱᴏ ʏᴏᴜʀ ꜰɪʟᴇꜱ ʟᴏᴏᴋ ᴄʟᴇᴀɴ ᴀɴᴅ ᴇᴀꜱʏ ᴛᴏ ʀᴇᴀᴅ.
"""
    
    keyboard = get_main_menu_keyboard(current_status)
    
    await message.reply_text(
        text=text, 
        reply_markup=keyboard, 
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^(on_metadata|off_metadata|set_metadata_menu|edit_|cancel_edit_|reset_all|metadata_home|meta_info|close_meta|clear_)"))
async def metadata_callback_handler(client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data
    
    # Handle toggle commands - NO NOTIFICATIONS
    if data == "on_metadata":
        await db.set_metadata(user_id, "On")
        await show_main_panel(query, user_id)
        return
    
    elif data == "off_metadata":
        await db.set_metadata(user_id, "Off")
        await show_main_panel(query, user_id)
        return
    
    # Handle "Set Metadata" menu
    elif data == "set_metadata_menu":
        # Don't edit if we're already on the set metadata menu
        if "Set Metadata Values" in query.message.text:
            return

        summary = await get_metadata_summary(user_id)
        
        text = f"""
**Your Metadata Is Currently: {current}**
{summary}
ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀᴋᴇ ᴄʜᴀɴɢᴇꜱ
"""
        keyboard = get_set_metadata_keyboard()
        await query.message.edit_text(text=text, reply_markup=keyboard)
        return
    
    # Handle edit field selection
    elif data.startswith("edit_"):
        field = data.split("_")[1]
        await show_edit_field_prompt(query, user_id, field)
        return
    
    # Handle cancel edit operation - DELETE WITH ANIMATION
    elif data.startswith("cancel_edit_"):
        field = data.split("_")[2]
        # Clear any editing state
        await db.col.update_one(
            {"_id": int(user_id)},
            {"$unset": {"editing_metadata_field": "", "editing_message_id": ""}}
        )
        # Delete message with animation
        await query.message.delete()
        return
    
    # Handle clearing field - NO NOTIFICATIONS
    elif data.startswith("clear_"):
        field = data.split("_")[1]
        field_display = field.capitalize()
        
        # Reset to default value
        default_values = {
            "title": "Encoded by @N4_Bots",
            "author": "@N4_Bots",
            "artist": "@N4_Bots",
            "audio": "By @N4_Bots",
            "subtitle": "By @N4_Bots",
            "video": "Encoded By @N4_Bots"
        }
        
        if field in default_values:
            method_name = f"set_{field}"
            method = getattr(db, method_name, None)
            if method:
                await method(user_id, default_values[field])
                await show_set_metadata_menu(query, user_id)
        return
    
    # Handle reset all - NO NOTIFICATIONS
    elif data == "reset_all":
        # Reset all fields to defaults
        await db.set_title(user_id, "Encoded by @N4_Bots")
        await db.set_author(user_id, "@N4_Bots")
        await db.set_artist(user_id, "@N4_Bots")
        await db.set_audio(user_id, "By @N4_Bots")
        await db.set_subtitle(user_id, "By @N4_Bots")
        await db.set_video(user_id, "Encoded By @N4_Bots")
        await show_set_metadata_menu(query, user_id)
        return
    
    # Handle back to home
    elif data == "metadata_home":
        await show_main_panel(query, user_id)
        return
    
    # Handle meta info/help
    elif data == "meta_info":
        if Txt.META_TXT in query.message.text:
            return
        await query.message.edit_text(
            text=Txt.META_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔙 Back", callback_data="set_metadata_menu"),
                    InlineKeyboardButton("Close", callback_data="close_meta")
                ]
            ])
        )
        return
    
    # Handle close - DELETE WITH ANIMATION
    elif data == "close_meta":
        await query.message.delete()
        return

async def show_edit_field_prompt(query, user_id, field):
    """Show edit prompt for a specific field"""
    field_display = field.capitalize()
    
    # Get current value
    method_name = f"get_{field}"
    method = getattr(db, method_name, None)
    current_value = await method(user_id) if method else "Not set"
    
    # Get example value
    examples = {
        "title": "Encoded By N4_Bots",
        "author": "N4_Bots",
        "artist": "N4_Bots",
        "audio": "N4_Bots",
        "subtitle": "N4_Bots",
        "video": "Encoded By N4_Bots"
    }
    example = examples.get(field, "Your custom value")
    
    text = f"""
**✏️ Send Me The New {field_display} Value:**

**Current {field_display}:** `{current_value}`

**Example:** `{example}`
"""
    
    keyboard = get_edit_field_keyboard(field)
    
    # Store which field we're editing and the message ID
    await db.col.update_one(
        {"_id": int(user_id)},
        {"$set": {
            "editing_metadata_field": field,
            "editing_message_id": query.message.id
        }}
    )
    
    await query.message.edit_text(text=text, reply_markup=keyboard)

async def show_main_panel(query, user_id):
    """Show the main metadata panel"""
    current_status = await db.get_metadata(user_id)
    summary = await get_metadata_summary(user_id)

    text = f"""
**Metadata Settings**

ᴛʜɪꜱ ʟᴇᴛꜱ ʏᴏᴜ ᴄʜᴀɴɢᴇ ᴛʜᴇ ɴᴀᴍᴇꜱ ᴀɴᴅ ᴅᴇᴛᴀɪʟꜱ ꜱʜᴏᴡɴ ᴏɴ ʏᴏᴜʀ ᴍᴇᴅɪᴀ ꜰɪʟᴇꜱ.

ʏᴏᴜ ᴄᴀɴ ᴇᴅɪᴛ ᴛʜɪɴɢꜱ ʟɪᴋᴇ ᴛɪᴛʟᴇ, ᴀᴜᴅɪᴏ ɴᴀᴍᴇ, ꜱᴜʙᴛɪᴛʟᴇ ɴᴀᴍᴇ, ᴀɴᴅ ᴀᴜᴛʜᴏʀ ꜱᴏ ʏᴏᴜʀ ꜰɪʟᴇꜱ ʟᴏᴏᴋ ᴄʟᴇᴀɴ ᴀɴᴅ ᴇᴀꜱʏ ᴛᴏ ʀᴇᴀᴅ.
"""
    
    keyboard = get_main_menu_keyboard(current_status)
    
    # Check if we're already showing this content to avoid MESSAGE_NOT_MODIFIED
    current_text = query.message.text
    if "Metadata Control Panel" in current_text and summary in current_text:
        # Content is the same, don't edit
        return
    summary = await get_metadata_summary(user_id)
    
    await query.message.edit_text(text=text, reply_markup=keyboard)

async def show_set_metadata_menu(query, user_id):
    """Show the set metadata menu"""
    text = f"""
{summary}
ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀᴋᴇ ᴄʜᴀɴɢᴇꜱ
"""
    keyboard = get_set_metadata_keyboard()
    
    # Check if we're already showing this content
    if "Set Metadata Values" in query.message.text:
        return
    
    await query.message.edit_text(text=text, reply_markup=keyboard)

@Client.on_message(filters.private & ~filters.command(EXCLUDED_COMMANDS))
async def handle_metadata_value_input(client, message):
    """Handle text input for metadata fields - SILENT UPDATE"""
    user_id = message.from_user.id
    
    # Check if user is in metadata editing mode
    user_data = await db.col.find_one({"_id": int(user_id)})
    if not user_data or "editing_metadata_field" not in user_data or "editing_message_id" not in user_data:
        return

    # FIX: Check if message.text exists before stripping
    if not message.text:
        try:
            # Optionally alert the user or just delete the non-text message
            await message.delete()
        except:
            pass
        return
        
    field = user_data["editing_metadata_field"]
    edit_message_id = user_data["editing_message_id"]
    new_value = message.text.strip()
    
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
        
        # Clear editing flag
        await db.col.update_one(
            {"_id": int(user_id)},
            {"$unset": {"editing_metadata_field": "", "editing_message_id": ""}}
        )
        
        # SILENT UPDATE: Edit the original prompt message with new current value
        field_display = field.capitalize()
        
        # Get updated current value
        get_method_name = f"get_{field}"
        get_method = getattr(db, get_method_name, None)
        current_value = await get_method(user_id) if get_method else "Not set"
        
        # Get example value
        examples = {
        "title": "Encoded By N4_Bots",
        "author": "N4_Bots",
        "artist": "N4_Bots",
        "audio": "N4_Bots",
        "subtitle": "N4_Bots",
        "video": "Encoded By N4_Bots"
        }
        example = examples.get(field, "Your custom value")
        
        # Update the original edit prompt message
        updated_text = f"""
**✏️ Send Me The New {field_display} Value:**

**Current {field_display}:** `{current_value}`

**Example:** `{example}`
"""
        
        keyboard = get_edit_field_keyboard(field)
        
        try:
            # Edit the original message using stored message ID
            await client.edit_message_text(
                chat_id=user_id,
                message_id=edit_message_id,
                text=updated_text,
                reply_markup=keyboard
            )
        except Exception as e:
            # If message not found or other error, just continue
            print(f"Error editing message: {e}")
        
        # Delete the user's input message
        try:
            await message.delete()
        except:
            pass

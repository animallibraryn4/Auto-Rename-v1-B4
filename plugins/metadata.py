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

async def clear_metadata_state(user_id):
    """Editing mode clear"""
    await db.col.update_one(
        {"_id": int(user_id)},
        {"$unset": {"editing_metadata_field": "", "editing_message_id": "", "editing_profile": ""}}
    )
    
async def get_metadata_summary(user_id, profile_num=None):
    """Generate a summary of metadata settings for a specific profile"""
    if profile_num is None:
        profile_num = await db.get_current_profile(user_id)
    
    current = await db.get_metadata(user_id)
    
    # Use profile-specific getters
    title = await db.get_metadata_field_with_profile(user_id, "title", profile_num)
    author = await db.get_metadata_field_with_profile(user_id, "author", profile_num)
    artist = await db.get_metadata_field_with_profile(user_id, "artist", profile_num)
    video = await db.get_metadata_field_with_profile(user_id, "video", profile_num)
    audio = await db.get_metadata_field_with_profile(user_id, "audio", profile_num)
    subtitle = await db.get_metadata_field_with_profile(user_id, "subtitle", profile_num)
    
    summary = f"""
**Current Profile: Profile {profile_num}** {'✅' if profile_num == await db.get_current_profile(user_id) else ''}

**Title:** `{title if title else 'Not Set'}`
**Author:** `{author if author else 'Not Set'}`
**Artist:** `{artist if artist else 'Not Set'}`
**Audio:** `{audio if audio else 'Not Set'}`
**Subtitle:** `{subtitle if subtitle else 'Not Set'}`
**Video:** `{video if video else 'Not Set'}`
"""
    return summary

def get_main_menu_keyboard(current_status):
    """Generate main menu keyboard WITHOUT profile buttons"""
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

def get_set_metadata_keyboard(current_profile):
    """Keyboard for setting metadata values WITH profile toggle button"""
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
            InlineKeyboardButton("View All", callback_data="view_all"),
            InlineKeyboardButton("Help", callback_data="meta_info")
        ],
        [
            InlineKeyboardButton(f"🔄 Switch {2 if current_profile == 1 else 1}", callback_data=f"toggle_profile"),
            InlineKeyboardButton("🔙 Back", callback_data="metadata_home")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_view_all_keyboard(current_profile):
    """Keyboard for View All Overview page WITH Switch Profile button"""
    buttons = [
        [
            InlineKeyboardButton(f"🔄 Switch {2 if current_profile == 1 else 1}", callback_data=f"toggle_profile_from_view")
        ],
        [
            InlineKeyboardButton("Close", callback_data="close_meta"),
            InlineKeyboardButton("🔙 Back", callback_data="set_metadata_menu")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_edit_field_keyboard(field, current_profile):
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
    current_profile = await db.get_current_profile(user_id)
    
    text = f"""
**Metadata Settings**

ᴛʜɪꜱ ʟᴇᴛꜱ ʏᴏᴜ ᴄʜᴀɴɢᴇ ᴛʜᴇ ɴᴀᴍᴇꜱ ᴀɴᴅ ᴅᴇᴛᴀɪʟꜱ ꜱʜᴏᴡɴ ᴏɴ ʏᴏᴜʀ ᴍᴇᴅɪᴀ ꜰɪʟᴇꜱ.

ʏᴏᴜ ᴄᴀɴ ꜱᴀᴠᴇ ᴛᴡᴏ ᴅɪꜰꜰᴇʀᴇɴᴛ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴘʀᴏꜰɪʟᴇꜱ ᴀɴᴅ ꜱᴡɪᴛᴄʜ ʙᴇᴛᴡᴇᴇɴ ᴛʜᴇᴍ ᴇᴀꜱɪʟʏ.

**Current Profile:** Profile {current_profile} {'✅' if current_profile == 1 else ''}
"""
    
    keyboard = get_main_menu_keyboard(current_status)
    
    await message.reply_text(
        text=text, 
        reply_markup=keyboard, 
        disable_web_page_preview=True
    )

# Change the callback handler decorator to be more specific:
METADATA_CALLBACK_PATTERNS = [
    'on_metadata', 'off_metadata', 'set_metadata_menu',
    'edit_title', 'edit_author', 'edit_artist', 'edit_audio',
    'edit_subtitle', 'edit_video', 'view_all', 'meta_info',
    'cancel_edit_', 'clear_', 'metadata_home', 'close_meta',
    'toggle_profile', 'toggle_profile_from_view'
]

# Create a regex pattern that matches metadata callbacks only
pattern = '|'.join(METADATA_CALLBACK_PATTERNS)
@Client.on_callback_query(filters.regex(f'^({pattern})$'))
async def metadata_callback_handler(client, query: CallbackQuery):
    # This will only handle metadata-specific callbacks
    user_id = query.from_user.id
    data = query.data
    current = await db.get_metadata(user_id)
    current_profile = await db.get_current_profile(user_id)
    
    # Handle toggle profile from View All page
    if data == "toggle_profile_from_view":
        # Toggle between profile 1 and 2
        new_profile = 2 if current_profile == 1 else 1
        await db.set_current_profile(user_id, new_profile)
        
        # Update the current overview message instead of opening new menu
        await show_all_profiles_overview(query, user_id)
        return
    
    # Handle regular toggle profile (from Set Metadata menu)
    elif data == "toggle_profile":
        # Toggle between profile 1 and 2
        new_profile = 2 if current_profile == 1 else 1
        await db.set_current_profile(user_id, new_profile)
        
        # Update the current message to show new profile
        current_profile = new_profile
        
        # Show updated set metadata menu
        await show_set_metadata_menu(query, user_id)
        return
    
    # Handle toggle commands - NO NOTIFICATIONS
    elif data == "on_metadata":
        await db.set_metadata(user_id, "On")
        await show_main_panel(query, user_id)
        return
    
    elif data == "off_metadata":
        await db.set_metadata(user_id, "Off")
        await show_main_panel(query, user_id)
        return
    
    # Handle "Set Metadata" menu
    elif data == "set_metadata_menu":
        await show_set_metadata_menu(query, user_id)
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
        await clear_metadata_state(user_id)
        # Delete message with animation
        await query.message.delete()
        return
    
    # Handle View All button
    elif data == "view_all":
        await show_all_profiles_overview(query, user_id)
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
            # Get current profile
            current_profile = await db.get_current_profile(user_id)
            # Reset profile-specific field
            await db.set_metadata_field_with_profile(user_id, field, default_values[field], current_profile)
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
                    InlineKeyboardButton("Close", callback_data="close_meta"),
                    InlineKeyboardButton("🔙 Back", callback_data="set_metadata_menu")
                ]
            ])
        )
        return
    
    # Handle close - DELETE WITH ANIMATION
    elif data == "close_meta":
        await query.message.delete()
        return
    
    # If no handler matched, answer with an error
    else:
        # Try to handle it with a simple answer
        await query.answer("Button not implemented yet", show_alert=True)

async def show_edit_field_prompt(query, user_id, field):
    """Show edit prompt for a specific field"""
    current_profile = await db.get_current_profile(user_id)
    field_display = field.capitalize()
    
    # Get current value with profile support
    current_value = await db.get_metadata_field_with_profile(user_id, field, current_profile)
    if not current_value:
        # Fallback to default
        method_name = f"get_{field}"
        method = getattr(db, method_name, None)
        if method:
            current_value = await method(user_id)
        else:
            current_value = "Not set"
    
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
**✏️ Send Me The New {field_display} Value**

**Current Profile:** Profile {current_profile}
**Current {field_display}:** `{current_value}`

**Example:** `{example}`
"""
    
    keyboard = get_edit_field_keyboard(field, current_profile)
    
    # Store which field we're editing and the message ID
    await db.col.update_one(
        {"_id": int(user_id)},
        {"$set": {
            "editing_metadata_field": field,
            "editing_message_id": query.message.id,
            "editing_profile": current_profile
        }}
    )
    
    await query.message.edit_text(text=text, reply_markup=keyboard)

async def show_main_panel(query, user_id):
    """Show the main metadata panel"""
    current_status = await db.get_metadata(user_id)
    current_profile = await db.get_current_profile(user_id)

    text = f"""
**Metadata Settings**

ᴛʜɪꜱ ʟᴇᴛꜱ ʏᴏᴜ ᴄʜᴀɴɢᴇ ᴛʜᴇ ɴᴀᴍᴇꜱ ᴀɴᴅ ᴅᴇᴛᴀɪʟꜱ ꜱʜᴏᴡɴ ᴏɴ ʏᴏᴜʀ ᴍᴇᴅɪᴀ ꜰɪʟᴇꜱ.

ʏᴏᴜ ᴄᴀɴ ꜱᴀᴠᴇ ᴛᴡᴏ ᴅɪꜰꜰᴇʀᴇɴᴛ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴘʀᴏꜰɪʟᴇꜱ ᴀɴᴅ ꜱᴡɪᴛᴄʜ ʙᴇᴛᴡᴇᴇɴ ᴛʜᴇᴍ ᴇᴀꜱɪʟʏ.

**Current Profile:** Profile {current_profile} {'✅' if current_profile == 1 else ''}
"""
    
    keyboard = get_main_menu_keyboard(current_status)
    
    await query.message.edit_text(text=text, reply_markup=keyboard)

async def show_set_metadata_menu(query, user_id):
    """Show the set metadata menu"""
    current = await db.get_metadata(user_id)
    current_profile = await db.get_current_profile(user_id)
    
    text = f"""
**Set Metadata Values**

**Current Status:** {current}
**Current Profile:** Profile {current_profile} {'✅'}

ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀᴋᴇ ᴄʜᴀɴɢᴇꜱ
"""
    keyboard = get_set_metadata_keyboard(current_profile)
    
    await query.message.edit_text(text=text, reply_markup=keyboard)

async def show_all_profiles_overview(query, user_id):
    """Show overview of both profiles"""
    profiles_summary = await db.get_all_profiles_summary(user_id)
    current_profile = await db.get_current_profile(user_id)
    
    text = "**📋 All Metadata Profiles Overview**\n\n"
    
    for profile_num in [1, 2]:
        profile_data = profiles_summary[f"profile_{profile_num}"]
        is_active = " ✅ (Active)" if profile_num == current_profile else ""
        
        text += f"**Profile {profile_num}**{is_active}\n"
        text += f"• **Title:** `{profile_data['title'] or 'Not Set'}`\n"
        text += f"• **Author:** `{profile_data['author'] or 'Not Set'}`\n"
        text += f"• **Artist:** `{profile_data['artist'] or 'Not Set'}`\n"
        text += f"• **Audio:** `{profile_data['audio'] or 'Not Set'}`\n"
        text += f"• **Subtitle:** `{profile_data['subtitle'] or 'Not Set'}`\n"
        text += f"• **Video:** `{profile_data['video'] or 'Not Set'}`\n\n"
    
    text += "ℹ️ *Go back to the Set Metadata menu to switch profiles.*"
    
    # Pass current_profile to the keyboard function
    keyboard = get_view_all_keyboard(current_profile)
    
    await query.message.edit_text(text=text, reply_markup=keyboard)

@Client.on_message(filters.private & ~filters.command(EXCLUDED_COMMANDS))
async def handle_metadata_value_input(client, message):
    """Handle text input for metadata fields with profile support - SILENT UPDATE"""
    user_id = message.from_user.id
    
    # Check if user is in metadata editing mode
    user_data = await db.col.find_one({"_id": int(user_id)})
    if not user_data or "editing_metadata_field" not in user_data or "editing_message_id" not in user_data:
        return

    # Check if message.text exists before stripping
    if not message.text:
        try:
            # Delete the non-text message
            await message.delete()
        except:
            pass
        return
        
    field = user_data["editing_metadata_field"]
    edit_message_id = user_data["editing_message_id"]
    editing_profile = user_data.get("editing_profile", await db.get_current_profile(user_id))
    new_value = message.text.strip()
    
    # Update the specific field with profile support
    success = await db.set_metadata_field_with_profile(user_id, field, new_value, editing_profile)
    
    if success:
        # Clear editing flag
        await clear_metadata_state(user_id)
        
        # SILENT UPDATE: Edit the original prompt message with new current value
        field_display = field.capitalize()
        
        # Get updated current value
        current_value = await db.get_metadata_field_with_profile(user_id, field, editing_profile)
        if not current_value:
            current_value = "Not set"
        
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
**✏️ Send Me The New {field_display} Value**

**Current Profile:** Profile {editing_profile}
**Current {field_display}:** `{current_value}`

**Example:** `{example}`
"""
        
        keyboard = get_edit_field_keyboard(field, editing_profile)
        
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
            pass
        
        # Delete the user's input message
        try:
            await message.delete()
        except:
            pass

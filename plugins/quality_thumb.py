from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import n4bots

QUALITY_TYPES = ["360p", "480p", "720p", "1080p", "HDrip", "2160p", "4K", "2K", "4kX264", "4kx265"]

async def generate_main_menu_buttons(user_id):
    buttons = []
    for i in range(0, len(QUALITY_TYPES), 3):
        row = QUALITY_TYPES[i:i+3]
        buttons.append([InlineKeyboardButton(q, f"quality_{q}") for q in row])
    
    buttons.extend([
        [InlineKeyboardButton("Global Thumb", "quality_global")],
        [InlineKeyboardButton("Delete All Thumbnails", "delete_all_thumbs")],
        [InlineKeyboardButton("Close", "quality_close")]
    ])
    return buttons

@Client.on_message(filters.private & filters.command("smart_thumb"))
async def quality_menu(client, message):
    # Check if user is banned
    from plugins.admin_panel import check_ban_status
    user_id = message.from_user.id
    if await check_ban_status(user_id):
        return
        
    buttons = await generate_main_menu_buttons(message.from_user.id)
    await message.reply_text(
        "🎬 Thumbnail Manager",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r'^quality_global$'))
async def global_thumb_menu(client, callback):
    user_id = callback.from_user.id
    has_thumb = await n4bots.get_global_thumb(user_id)
    is_enabled = await n4bots.is_global_thumb_enabled(user_id)
    
    buttons = [
        [InlineKeyboardButton("👀 View Global Thumb", "view_global")],
        [InlineKeyboardButton("🖼️ Set Global Thumb", "set_global")],
        [InlineKeyboardButton("🗑 Delete Global Thumb", "delete_global")],
        [InlineKeyboardButton(f"🌐 Global Mode: {'ON ✅' if is_enabled else 'OFF ❌'}", "toggle_global_mode")],
        [InlineKeyboardButton("🔙 Main Menu", "back_to_main")]
    ]
    
    status_text = f"Status: {'✅ Set' if has_thumb else '❌ Not Set'}\nMode: {'🌐 Enabled' if is_enabled else '🚫 Disabled'}"
    await callback.message.edit_text(
        f"⚙️ Global Thumbnail Settings\n\n{status_text}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r'^toggle_global_mode$'))
async def toggle_global_mode(client, callback):
    user_id = callback.from_user.id
    new_status = not await n4bots.is_global_thumb_enabled(user_id)
    await n4bots.toggle_global_thumb(user_id, new_status)
    await global_thumb_menu(client, callback)
    await callback.answer(f"Global Mode {'Enabled' if new_status else 'Disabled'}")

@Client.on_callback_query(filters.regex(r'^set_global$'))
async def set_global_thumb(client, callback):
    user_id = callback.from_user.id
    await n4bots.set_temp_quality(user_id, "global")
    await callback.message.edit_text(
        "🖼️ **Send me the Global Thumbnail**\n\nPlease send a **photo** (not a document) to set as global thumbnail.\n\n⚠️ Note: Send as photo, not as document!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Cancel", "quality_global")]
        ])
    )

# HIGH PRIORITY PHOTO HANDLER
@Client.on_message(filters.private & filters.photo, group=1)
async def save_thumbnail_priority(client, message):
    user_id = message.from_user.id
    quality = await n4bots.get_temp_quality(user_id)
    
    if not quality:
        # No temp quality set, not for thumbnail
        print(f"No temp quality set for user {user_id}, passing to next handler")
        return
    
    try:
        # Check if user is in metadata editing mode
        user_data = await n4bots.col.find_one({"_id": int(user_id)})
        if user_data and "editing_metadata_field" in user_data:
            print(f"User {user_id} is in metadata editing mode, checking if this is thumbnail...")
            
            # If user has temp_quality set, they're trying to set thumbnail, not metadata
            # So we should save the thumbnail and clear the metadata editing state
            if quality:
                print(f"User {user_id} has temp_quality set, saving thumbnail and clearing metadata state")
                # Clear metadata editing state
                await n4bots.col.update_one(
                    {"_id": int(user_id)},
                    {"$unset": {"editing_metadata_field": "", "editing_message_id": ""}}
                )
            else:
                # No temp_quality, let metadata.py handle it
                print(f"No temp_quality for user {user_id}, passing to metadata handler")
                return
        
        print(f"Saving thumbnail for user {user_id}, quality: {quality}")
        
        if quality == "global":
            # Set global thumbnail
            await n4bots.col.update_one(
                {"_id": user_id},
                {"$set": {"global_thumb": message.photo.file_id}}
            )
            reply_text = "✅ **Global thumbnail saved successfully!**\n\nAll quality-specific thumbnails are disabled when global thumb is active."
            
            # Send success message with buttons
            await message.reply_text(
                reply_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👀 View Thumbnail", f"view_{quality}")],
                    [InlineKeyboardButton("⚙️ Settings", f"quality_{quality}")]
                ])
            )
            
        else:
            if await n4bots.is_global_thumb_enabled(user_id):
                await message.reply_text("❌ **Global mode is active!**\n\nPlease disable Global Mode first from Global Thumbnail Settings to set quality-specific thumbnails.")
                await n4bots.clear_temp_quality(user_id)
                return
                
            # Save quality-specific thumbnail
            await n4bots.set_quality_thumbnail(user_id, quality, message.photo.file_id)
            reply_text = f"✅ **{quality.upper()} thumbnail saved successfully!**"
            
            # Get current quality index for navigation
            current_index = QUALITY_TYPES.index(quality) if quality in QUALITY_TYPES else -1
            
            # Create navigation buttons
            nav_buttons = []
            if current_index >= 0:
                # Add navigation buttons only if current quality is in QUALITY_TYPES
                prev_index = (current_index - 1) % len(QUALITY_TYPES)
                next_index = (current_index + 1) % len(QUALITY_TYPES)
                
                prev_quality = QUALITY_TYPES[prev_index]
                next_quality = QUALITY_TYPES[next_index]
                
                nav_buttons = [
                    [InlineKeyboardButton("◀️ Previous", f"set_{prev_quality}"),
                     InlineKeyboardButton("▶️ Next", f"set_{next_quality}")]
                ]
            
            # Add view and settings buttons
            action_buttons = [
                [InlineKeyboardButton("👀 View Thumbnail", f"view_{quality}")],
                [InlineKeyboardButton("⚙️ Settings", f"quality_{quality}")]
            ]
            
            # Combine all buttons
            all_buttons = nav_buttons + action_buttons
            
            # Send success message with navigation buttons
            await message.reply_text(
                reply_text,
                reply_markup=InlineKeyboardMarkup(all_buttons)
            )
        
        # Clear temp quality
        await n4bots.clear_temp_quality(user_id)
            
    except Exception as e:
        print(f"❌ Error saving thumbnail: {e}")
        await message.reply_text(f"❌ **Error saving thumbnail:**\n`{str(e)}`")
        await n4bots.clear_temp_quality(user_id)

@Client.on_callback_query(filters.regex(r'^view_global$'))
async def view_global_thumb(client, callback):
    user_id = callback.from_user.id
    thumb = await n4bots.get_global_thumb(user_id)
    if thumb:
        await client.send_photo(
            callback.message.chat.id,
            photo=thumb,
            caption="📸 **Global Thumbnail**"
        )
    else:
        await callback.answer("No global thumbnail set!", show_alert=True)

@Client.on_callback_query(filters.regex(r'^delete_global$'))
async def delete_global_thumb(client, callback):
    user_id = callback.from_user.id
    await n4bots.set_global_thumb(user_id, None)
    await callback.message.edit_text(
        "🗑 **Global thumbnail deleted!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", "quality_global")]
        ])
    )

@Client.on_callback_query(filters.regex('^back_to_main$'))
async def back_to_main(client, callback):
    buttons = await generate_main_menu_buttons(callback.from_user.id)
    await callback.message.edit_text(
        "🎬 **Thumbnail Manager**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex('^delete_all_thumbs$'))
async def delete_all_thumbs(client, callback):
    user_id = callback.from_user.id
    await n4bots.col.update_one(
        {"_id": user_id},
        {"$set": {"thumbnails": {}}, "$unset": {"global_thumb": ""}}
    )
    await callback.message.edit_text(
        "✅ **All thumbnails deleted successfully!**",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Main Menu", "back_to_main")]
        ])
    )

@Client.on_callback_query(filters.regex(r'^quality_([a-zA-Z0-9]+)$'))
async def quality_handler(client, callback):
    user_id = callback.from_user.id
    quality = callback.matches[0].group(1)
    
    if quality == "close":
        await callback.message.delete()
        return
    
    if quality == "global":
        await global_thumb_menu(client, callback)
        return
    
    is_global = await n4bots.is_global_thumb_enabled(user_id)
    has_thumb = await n4bots.get_quality_thumbnail(user_id, quality)
    
    # Create buttons in the specified format
    buttons = [
        [InlineKeyboardButton("🖼️ Set New", f"set_{quality}")],
        [InlineKeyboardButton("👀 View", f"view_{quality}")],
        [InlineKeyboardButton("🗑 Delete", f"delete_{quality}")],
        [InlineKeyboardButton("🌐 Global", "quality_global")],
        [InlineKeyboardButton("◀️", f"prev_{quality}"),
         InlineKeyboardButton("▶️", f"next_{quality}")],
        [InlineKeyboardButton("🔙 Main Menu", "back_to_main")]
    ]
    
    status_text = "🌐 (Global Mode Active)" if is_global else f"{'✅ Set' if has_thumb else '❌ Not Set'}"
    await callback.message.edit_text(
        f"⚙️ **{quality.upper()} Settings**\n\n**Status:** {status_text}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r'^prev_([a-zA-Z0-9]+)$'))
async def prev_quality_handler(client, callback):
    """Navigate to previous quality"""
    user_id = callback.from_user.id
    current_quality = callback.matches[0].group(1)
    
    if current_quality not in QUALITY_TYPES:
        return
    
    # Get previous quality
    current_index = QUALITY_TYPES.index(current_quality)
    prev_index = (current_index - 1) % len(QUALITY_TYPES)
    new_quality = QUALITY_TYPES[prev_index]
    
    # Show the new quality menu
    is_global = await n4bots.is_global_thumb_enabled(user_id)
    has_thumb = await n4bots.get_quality_thumbnail(user_id, new_quality)
    
    # Create buttons for the new quality
    buttons = [
        [InlineKeyboardButton("🖼️ Set New", f"set_{new_quality}")],
        [InlineKeyboardButton("👀 View", f"view_{new_quality}")],
        [InlineKeyboardButton("🗑 Delete", f"delete_{new_quality}")],
        [InlineKeyboardButton("🌐 Global", "quality_global")],
        [InlineKeyboardButton("◀️", f"prev_{new_quality}"),
         InlineKeyboardButton("▶️", f"next_{new_quality}")],
        [InlineKeyboardButton("🔙 Main Menu", "back_to_main")]
    ]
    
    status_text = "🌐 (Global Mode Active)" if is_global else f"{'✅ Set' if has_thumb else '❌ Not Set'}"
    await callback.message.edit_text(
        f"⚙️ **{new_quality.upper()} Settings**\n\n**Status:** {status_text}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r'^next_([a-zA-Z0-9]+)$'))
async def next_quality_handler(client, callback):
    """Navigate to next quality"""
    user_id = callback.from_user.id
    current_quality = callback.matches[0].group(1)
    
    if current_quality not in QUALITY_TYPES:
        return
    
    # Get next quality
    current_index = QUALITY_TYPES.index(current_quality)
    next_index = (current_index + 1) % len(QUALITY_TYPES)
    new_quality = QUALITY_TYPES[next_index]
    
    # Show the new quality menu
    is_global = await n4bots.is_global_thumb_enabled(user_id)
    has_thumb = await n4bots.get_quality_thumbnail(user_id, new_quality)
    
    # Create buttons for the new quality
    buttons = [
        [InlineKeyboardButton("🖼️ Set New", f"set_{new_quality}")],
        [InlineKeyboardButton("👀 View", f"view_{new_quality}")],
        [InlineKeyboardButton("🗑 Delete", f"delete_{new_quality}")],
        [InlineKeyboardButton("🌐 Global", "quality_global")],
        [InlineKeyboardButton("◀️", f"prev_{new_quality}"),
         InlineKeyboardButton("▶️", f"next_{new_quality}")],
        [InlineKeyboardButton("🔙 Main Menu", "back_to_main")]
    ]
    
    status_text = "🌐 (Global Mode Active)" if is_global else f"{'✅ Set' if has_thumb else '❌ Not Set'}"
    await callback.message.edit_text(
        f"⚙️ **{new_quality.upper()} Settings**\n\n**Status:** {status_text}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r'^set_([a-zA-Z0-9]+)$'))
async def set_thumbnail_handler(client, callback):
    user_id = callback.from_user.id
    quality = callback.matches[0].group(1)
    await n4bots.set_temp_quality(user_id, quality)
    
    # Get current quality index for navigation display
    current_index = QUALITY_TYPES.index(quality) if quality in QUALITY_TYPES else -1
    total_count = len(QUALITY_TYPES)
    
    navigation_info = ""
    if current_index >= 0:
        navigation_info = f"\n\n📋 **{current_index + 1}/{total_count}** - Use ◀️/▶️ buttons to navigate"
    
    await callback.message.edit_text(
        f"🖼️ **Send {quality.upper()} Thumbnail**\n\nPlease send a **photo** (not a document) to set as {quality.upper()} thumbnail.{navigation_info}\n\n⚠️ Note: Send as photo, not as document!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Cancel", f"quality_{quality}")]
        ])
    )

@Client.on_callback_query(filters.regex(r'^view_([a-zA-Z0-9]+)$'))
async def view_thumbnail(client, callback):
    user_id = callback.from_user.id
    quality = callback.matches[0].group(1)
    
    if quality == "global":
        thumb = await n4bots.get_global_thumb(user_id)
    elif await n4bots.is_global_thumb_enabled(user_id):
        thumb = await n4bots.get_global_thumb(user_id)
    else:
        thumb = await n4bots.get_quality_thumbnail(user_id, quality)
    
    if thumb:
        await client.send_photo(
            callback.message.chat.id,
            photo=thumb,
            caption=f"📸 **{quality.upper()} Thumbnail**{' (Global)' if await n4bots.is_global_thumb_enabled(user_id) else ''}"
        )
    else:
        await callback.answer("No thumbnail set!", show_alert=True)

@Client.on_callback_query(filters.regex(r'^delete_([a-zA-Z0-9]+)$'))
async def delete_thumbnail(client, callback):
    user_id = callback.from_user.id
    quality = callback.matches[0].group(1)
    
    if quality == "global":
        await n4bots.set_global_thumb(user_id, None)
        reply_text = "🗑 **Global thumbnail deleted!**"
    elif await n4bots.is_global_thumb_enabled(user_id):
        await callback.answer("Global mode is active!", show_alert=True)
        return
    else:
        await n4bots.set_quality_thumbnail(user_id, quality, None)
        reply_text = f"🗑 **{quality.upper()} thumbnail deleted!**"
    
    await callback.message.edit_text(
        reply_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", f"quality_{quality}")]
        ])
    )

# Handler to clear temp quality when user cancels
@Client.on_callback_query(filters.regex(r'^quality_(360p|480p|720p|1080p|HDrip|2160p|4K|2K|4kX264|4kx265|global)$'))
async def quality_cancel_handler(client, callback):
    """Clear temp quality and metadata editing state when user navigates away from set thumbnail screen"""
    user_id = callback.from_user.id
    await n4bots.clear_temp_quality(user_id)
    
    # Also clear metadata editing state if it exists
    await n4bots.col.update_one(
        {"_id": int(user_id)},
        {"$unset": {"editing_metadata_field": "", "editing_message_id": ""}}
    )
    
    quality = callback.data.split('_')[1]
    if quality == "global":
        await global_thumb_menu(client, callback)
    else:
        await quality_handler(client, callback)
        


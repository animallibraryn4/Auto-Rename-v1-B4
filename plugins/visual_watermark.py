import os
import tempfile
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from helper.database import codeflixbots

# Position options for watermark
POSITION_OPTIONS = {
    "top-left": "Top Left",
    "top-right": "Top Right", 
    "bottom-left": "Bottom Left",
    "bottom-right": "Bottom Right",
    "center": "Center"
}

@Client.on_message(filters.private & filters.command(["setwatermark", "set_watermark"]))
async def set_watermark_menu(client, message: Message):
    """Show watermark setup menu"""
    user_id = message.from_user.id
    current_settings = await codeflixbots.get_video_watermark(user_id)
    
    is_enabled = current_settings.get("enabled", False)
    watermark_type = current_settings.get("type", "text")
    
    text = f"""
🎬 **Video Watermark Settings**

**Status:** {'✅ Enabled' if is_enabled else '❌ Disabled'}
**Type:** {watermark_type.title()}
"""
    
    if is_enabled and watermark_type == "text":
        watermark_text = current_settings.get("text", "")
        position = current_settings.get("position", "bottom-right")
        text += f"**Text:** `{watermark_text}`\n"
        text += f"**Position:** `{position}`\n"
    elif is_enabled and watermark_type == "image":
        text += "**Type:** Image Watermark\n"
        text += f"**Position:** `{current_settings.get('position', 'bottom-right')}`\n"
    
    text += "\n**Choose an option:**"
    
    buttons = [
        [InlineKeyboardButton("📝 Set Text Watermark", callback_data="watermark_set_text")],
        [InlineKeyboardButton("🖼️ Set Image Watermark", callback_data="watermark_set_image")],
        [InlineKeyboardButton("⚙️ Configure Position", callback_data="watermark_position")],
        [InlineKeyboardButton("👁️ Preview Watermark", callback_data="watermark_preview")],
        [InlineKeyboardButton("❌ Disable Watermark", callback_data="watermark_disable")],
        [InlineKeyboardButton("📖 Help", callback_data="watermark_help")]
    ]
    
    await message.reply_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^watermark_set_text$"))
async def set_text_watermark_handler(client, query: CallbackQuery):
    """Handle text watermark setup"""
    await query.message.edit_text(
        "📝 **Set Text Watermark**\n\n"
        "Send me the text you want to use as a watermark.\n\n"
        "💡 **Tips for better performance:**\n"
        "• Keep text short (max 50 characters)\n"
        "• Avoid complex unicode characters\n"
        "• Simple fonts work faster\n\n"
        "**Example:** `@Animelibraryn4`\n"
        "**Format:** Just send the text message",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="watermark_back")]
        ])
    )
    
    await codeflixbots.set_temp_quality(query.from_user.id, "awaiting_watermark_text")

@Client.on_message(filters.private & filters.text)
async def handle_watermark_text(client, message: Message):
    """Handle watermark text input"""
    user_id = message.from_user.id
    temp_state = await codeflixbots.get_temp_quality(user_id)
    
    if temp_state == "awaiting_watermark_text":
        watermark_text = message.text
        
        # Store the text temporarily
        await codeflixbots.set_temp_quality(user_id, f"watermark_text:{watermark_text}")
        
        # Ask for position
        buttons = []
        for pos_key, pos_name in POSITION_OPTIONS.items():
            buttons.append([InlineKeyboardButton(pos_name, callback_data=f"watermark_pos_{pos_key}")])
        
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="watermark_back")])
        
        await message.reply_text(
            f"✅ **Text saved:** `{watermark_text}`\n\n"
            "📌 **Now select watermark position:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@Client.on_callback_query(filters.regex(r"^watermark_pos_"))
async def set_watermark_position(client, query: CallbackQuery):
    """Set watermark position"""
    user_id = query.from_user.id
    position = query.data.split("_")[2]  # Extract position from callback
    
    # Get stored text
    temp_state = await codeflixbots.get_temp_quality(user_id)
    
    if temp_state and temp_state.startswith("watermark_text:"):
        watermark_text = temp_state.split(":", 1)[1]
        
        # Save watermark settings
        await codeflixbots.set_text_watermark(
            user_id=user_id,
            text=watermark_text,
            position=position
        )
        
        await query.message.edit_text(
            f"✅ **Watermark set successfully!**\n\n"
            f"**Text:** `{watermark_text}`\n"
            f"**Position:** `{position}`\n\n"
            "Your watermark will now appear on all video files you rename.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁️ Preview", callback_data="watermark_preview")],
                [InlineKeyboardButton("🔙 Back", callback_data="watermark_back")]
            ])
        )
        
        # Clear temp state
        await codeflixbots.clear_temp_quality(user_id)

@Client.on_callback_query(filters.regex(r"^watermark_set_image$"))
async def set_image_watermark_handler(client, query: CallbackQuery):
    """Handle image watermark setup"""
    await query.message.edit_text(
        "🖼️ **Set Image Watermark**\n\n"
        "Send me the image/logo you want to use as a watermark.\n\n"
        "**Requirements:**\n"
        "• PNG with transparent background recommended\n"
        "• Small size (200x200 pixels or less)\n"
        "• Send as photo (not document)\n\n"
        "After sending image, I'll ask for position settings.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="watermark_back")]
        ])
    )
    
    # Store state
    await codeflixbots.set_temp_quality(query.from_user.id, "awaiting_watermark_image")

@Client.on_message(filters.private & filters.photo)
async def handle_watermark_image(client, message: Message):
    """Handle image watermark input"""
    user_id = message.from_user.id
    temp_state = await codeflixbots.get_temp_quality(user_id)
    
    if temp_state == "awaiting_watermark_image":
        # Download the image
        image_path = f"watermarks/{user_id}_watermark.png"
        os.makedirs("watermarks", exist_ok=True)
        
        await client.download_media(message.photo.file_id, file_name=image_path)
        
        # Store image path temporarily
        await codeflixbots.set_temp_quality(user_id, f"watermark_image:{image_path}:{message.photo.file_id}")
        
        # Ask for position
        buttons = []
        for pos_key, pos_name in POSITION_OPTIONS.items():
            buttons.append([InlineKeyboardButton(pos_name, callback_data=f"watermark_imgpos_{pos_key}")])
        
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="watermark_back")])
        
        await message.reply_text(
            "✅ **Image saved!**\n\n"
            "📌 **Now select watermark position:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@Client.on_callback_query(filters.regex(r"^watermark_imgpos_"))
async def set_image_watermark_position(client, query: CallbackQuery):
    """Set image watermark position"""
    user_id = query.from_user.id
    position = query.data.split("_")[2]  # Extract position
    
    # Get stored image info
    temp_state = await codeflixbots.get_temp_quality(user_id)
    
    if temp_state and temp_state.startswith("watermark_image:"):
        parts = temp_state.split(":")
        image_path = parts[1]
        image_file_id = parts[2]
        
        # Save watermark settings
        await codeflixbots.set_image_watermark(
            user_id=user_id,
            image_file_id=image_file_id,
            position=position
        )
        
        await query.message.edit_text(
            f"✅ **Image watermark set successfully!**\n\n"
            f"**Position:** `{position}`\n\n"
            "Your watermark will now appear on all video files you rename.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁️ Preview", callback_data="watermark_preview")],
                [InlineKeyboardButton("🔙 Back", callback_data="watermark_back")]
            ])
        )
        
        # Clear temp state
        await codeflixbots.clear_temp_quality(user_id)

@Client.on_callback_query(filters.regex(r"^watermark_preview$"))
async def preview_watermark(client, query: CallbackQuery):
    """Show watermark preview"""
    user_id = query.from_user.id
    settings = await codeflixbots.get_video_watermark(user_id)
    
    if not settings.get("enabled"):
        await query.answer("Watermark is not enabled!", show_alert=True)
        return
    
    watermark_type = settings.get("type", "text")
    position = settings.get("position", "bottom-right")
    
    preview_text = f"""
🎬 **Watermark Preview**

**Status:** ✅ Enabled
**Type:** {watermark_type.title()}
**Position:** {position}
"""
    
    if watermark_type == "text":
        preview_text += f"**Text:** `{settings.get('text', '')}`\n"
    elif watermark_type == "image":
        preview_text += "**Type:** Image Watermark\n"
    
    preview_text += "\n**Position Mapping:**\n"
    preview_text += "┌───────┬───────┐\n"
    preview_text += "│Top-Left│Top-Right│\n"
    preview_text += "├───────┼───────┤\n"
    preview_text += "│Bottom-L│Bottom-R│\n"
    preview_text += "└───────┴───────┘\n\n"
    preview_text += f"Your watermark will appear at: **{position}**"
    
    await query.message.edit_text(
        text=preview_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Change Settings", callback_data="watermark_back")],
            [InlineKeyboardButton("🔙 Back", callback_data="watermark_back")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^watermark_disable$"))
async def disable_watermark_handler(client, query: CallbackQuery):
    """Disable watermark"""
    user_id = query.from_user.id
    await codeflixbots.disable_watermark(user_id)
    
    await query.message.edit_text(
        "✅ **Watermark disabled successfully!**\n\n"
        "Video files will no longer have watermarks added.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="watermark_back")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^watermark_help$"))
async def watermark_help_handler(client, query: CallbackQuery):
    """Show watermark help"""
    help_text = """
🖼️ **Video Watermark Feature**

Add a visible watermark (text or logo) to your video files.

**Commands:**
• `/setwatermark` - Open watermark settings
• `/watermark` - Show this help

**Features:**
1. **Text Watermark** - Add custom text
2. **Image Watermark** - Add logo/image
3. **Position Control** - Choose corner position
4. **Opacity Control** - Adjust transparency

**Supported Positions:**
• Top Left • Top Right
• Bottom Left • Bottom Right
• Center

**How it works:**
1. Set your watermark (text or image)
2. Choose position
3. When you rename videos, watermark is automatically embedded
4. Works with all video formats

**Requirements for images:**
• PNG format (transparent background)
• Small size recommended
• Square aspect ratio works best
"""
    
    await query.message.edit_text(
        text=help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Open Settings", callback_data="watermark_back")],
            [InlineKeyboardButton("🔙 Back", callback_data="watermark_back")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^watermark_back$"))
async def watermark_back_handler(client, query: CallbackQuery):
    """Go back to watermark menu"""
    await set_watermark_menu(client, query.message)

@Client.on_message(filters.private & filters.command(["watermark"]))
async def watermark_help_command(client, message: Message):
    """Watermark help command"""
    await watermark_help_handler(client, message)

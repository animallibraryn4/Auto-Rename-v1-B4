from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import codeflixbots

@Client.on_message(filters.private & filters.command("mode"))
async def mode_command(client, message):
    """Switch between File Mode and Caption Mode"""
    user_id = message.from_user.id
    current_mode = await codeflixbots.get_rename_mode(user_id)
    
    text = f"""
**🔧 Rename Mode Settings**

**Current Mode:** `{current_mode.upper()} MODE`

**📁 File Mode:**
- Extracts season/episode/quality from **file name**
- Ignores the caption completely
- Best for files with metadata in filename

**📝 Caption Mode:**
- Extracts season/episode/quality from **file caption**
- Ignores the file name completely
- Best when caption contains metadata

**How to use:**
1. Click buttons below to switch mode
2. Send files with appropriate metadata source
3. The bot will auto-rename based on selected mode
"""
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"📁 File Mode {'✅' if current_mode == 'file' else ''}",
                callback_data="mode_file"
            )
        ],
        [
            InlineKeyboardButton(
                f"📝 Caption Mode {'✅' if current_mode == 'caption' else ''}",
                callback_data="mode_caption"
            )
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]
    ])
    
    await message.reply_text(
        text=text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r'^mode_(file|caption)$'))
async def mode_callback(client, callback_query):
    user_id = callback_query.from_user.id
    mode = callback_query.data.split("_")[1]  # "file" or "caption"
    
    await codeflixbots.set_rename_mode(user_id, mode)
    
    # Update the message with new mode
    text = f"""
**🔧 Rename Mode Settings**

**Current Mode:** `{mode.upper()} MODE` ✅

**📁 File Mode:**
- Extracts season/episode/quality from **file name**
- Ignores the caption completely
- Best for files with metadata in filename

**📝 Caption Mode:**
- Extracts season/episode/quality from **file caption**
- Ignores the file name completely
- Best when caption contains metadata

**How to use:**
1. Click buttons below to switch mode
2. Send files with appropriate metadata source
3. The bot will auto-rename based on selected mode
"""
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"📁 File Mode {'✅' if mode == 'file' else ''}",
                callback_data="mode_file"
            )
        ],
        [
            InlineKeyboardButton(
                f"📝 Caption Mode {'✅' if mode == 'caption' else ''}",
                callback_data="mode_caption"
            )
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="close")
        ]
    ])
    
    await callback_query.message.edit_text(
        text=text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )
    
    await callback_query.answer(f"Switched to {mode.upper()} Mode!")

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from helper.database import n4bots
from config import Txt

@Client.on_message(filters.command("panel")) # filters.user filter ko temporary hata dein
async def vpanel_command(client, message):
    print(f"Command received from: {message.from_user.id}") # Terminal check ke liye
    await message.reply_text("Vpanel check!")

@Client.on_message(filters.private & filters.command("mode"))
async def mode_command(client, message: Message):
    """Handle /mode command to switch between File Mode and Caption Mode"""
    user_id = message.from_user.id
    current_mode = await n4bots.get_mode(user_id)
    
    text = f"""
📊 **Current Mode:** `{current_mode.replace('_', ' ').title()}`

**🔹 File Mode:**
• Extracts season, episode, and quality from **file name**
• Ignores file caption
• Best for files with proper naming patterns

**🔸 Caption Mode:**
• Extracts season, episode, and quality from **file caption**
• Ignores file name
• Best for files where caption contains the information

**Choose your preferred mode:**
"""
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"📁 File Mode {'✅' if current_mode == 'file_mode' else ''}",
                callback_data="set_mode_file"
            )
        ],
        [
            InlineKeyboardButton(
                f"📝 Caption Mode {'✅' if current_mode == 'caption_mode' else ''}",
                callback_data="set_mode_caption"
            )
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="close_mode")
        ]
    ])
    
    await message.reply_text(
        text=text,
        reply_markup=buttons,
        disable_web_page_preview=True
    )

@Client.on_callback_query(filters.regex(r"^set_mode_"))
async def set_mode_callback(client, query: CallbackQuery):
    """Handle mode selection callback"""
    user_id = query.from_user.id
    mode = query.data.split("_")[2]  # file or caption
    
    if mode in ["file", "caption"]:
        mode_value = f"{mode}_mode"
        await n4bots.set_mode(user_id, mode_value)
        
        # Update the message with new mode
        text = f"""
✅ **Mode Updated Successfully!**

📊 **New Mode:** `{mode_value.replace('_', ' ').title()}`

**{'• Extracts information from file names' if mode == 'file' else '• Extracts information from file captions'}**
**{'• Ignores file captions' if mode == 'file' else '• Ignores file names'}**

You can now send files for renaming in **{mode_value.replace('_', ' ').title()}**.
"""
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📁 File Mode", callback_data="set_mode_file"),
                InlineKeyboardButton("📝 Caption Mode", callback_data="set_mode_caption")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close_mode")
            ]
        ])
        
        await query.message.edit_text(
            text=text,
            reply_markup=buttons,
            disable_web_page_preview=True
        )
        
        await query.answer(f"Switched to {mode_value.replace('_', ' ').title()}")

@Client.on_callback_query(filters.regex("^close_mode$"))
async def close_mode_callback(client, query: CallbackQuery):
    """Close mode selection message"""
    await query.message.delete()

async def get_user_mode(user_id):
    """Get user mode preference - integrates with sequence.py"""
    # First check if user has sequence mode set
    if user_id in user_sequences:
        mode_type = user_mode.get(user_id, "file")
        return f"sequence_{mode_type}"
    
    # Otherwise get from database
    db_mode = await n4bots.get_mode(user_id)
    return db_mode if db_mode else "file_mode"

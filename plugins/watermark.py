from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from helper.database import codeflixbots

@Client.on_message(filters.private & filters.command(["setname", "set_name"]))
async def set_watermark_command(client, message: Message):
    """Set watermark text to be added to file names"""
    if len(message.command) < 2:
        await message.reply_text(
            "**❓ How to use /setname**\n\n"
            "**To set watermark:** `/setname [Your Watermark Text]`\n"
            "**Example:** `/setname @Animelibraryn4`\n\n"
            "**To remove watermark:** `/delname`\n"
            "**To view current watermark:** `/viewname`\n\n"
            "📝 *Note:* Watermark will be added at the end of the filename before extension."
        )
        return
    
    watermark_text = " ".join(message.command[1:])
    
    # Save watermark to database
    await codeflixbots.set_watermark(message.from_user.id, watermark_text)
    
    await message.reply_text(
        f"✅ **Watermark set successfully!**\n\n"
        f"**Watermark:** `{watermark_text}`\n\n"
        f"📁 *Example filename:*\n"
        f"Original: `MyFile.mkv`\n"
        f"With watermark: `MyFile {watermark_text}.mkv`"
    )

@Client.on_message(filters.private & filters.command(["delname", "del_name"]))
async def delete_watermark_command(client, message: Message):
    """Delete user's watermark"""
    current_watermark = await codeflixbots.get_watermark(message.from_user.id)
    
    if not current_watermark:
        await message.reply_text("❌ **No watermark is currently set!**")
        return
    
    await codeflixbots.delete_watermark(message.from_user.id)
    await message.reply_text("✅ **Watermark deleted successfully!**\n\nFiles will no longer have watermark added.")

@Client.on_message(filters.private & filters.command(["viewname", "view_name"]))
async def view_watermark_command(client, message: Message):
    """View current watermark"""
    current_watermark = await codeflixbots.get_watermark(message.from_user.id)
    
    if not current_watermark:
        await message.reply_text("❌ **No watermark is currently set!**\n\nUse `/setname [text]` to add a watermark.")
        return
    
    await message.reply_text(
        f"✅ **Current Watermark:**\n\n"
        f"`{current_watermark}`\n\n"
        f"📁 *Example filename:*\n"
        f"Original: `MyFile.mkv`\n"
        f"With watermark: `MyFile {current_watermark}.mkv`\n\n"
        f"*Use `/delname` to remove watermark*"
    )

@Client.on_message(filters.private & filters.command(["watermark", "watermark_help"]))
async def watermark_help_command(client, message: Message):
    """Show watermark help"""
    await message.reply_text(
        "🖊️ **Watermark Feature Help**\n\n"
        "**Commands:**\n"
        "• `/setname [text]` - Add watermark to file names\n"
        "• `/delname` - Remove watermark\n"
        "• `/viewname` - View current watermark\n\n"
        "**How it works:**\n"
        "1. Set your watermark text (e.g., `@Animelibraryn4`)\n"
        "2. When you rename files, the watermark is automatically added\n"
        "3. Example: `Naruto S01E01.mkv` → `Naruto S01E01 @Animelibraryn4.mkv`\n\n"
        "**Note:** Watermark is added at the end, before the file extension."
    )

from plugins import validate_token 
import random
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from helper.database import n4bots
from config import *
from config import Config

# Import the check_ban_status function from admin_panel
from plugins.admin_panel import check_ban_status

# Start Command Handler
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message: Message):
    # ADD THIS BAN CHECK AT THE BEGINNING
    from plugins.admin_panel import check_ban_status
    is_banned = await check_ban_status(client, message)
    if is_banned:
        return
        
    if hasattr(message, 'command') and len(message.command) == 2: 
       data = message.command[1]
       if data.split("-")[0] == 'verify':
           await validate_token(client, message, data)
           return
    
    user = message.from_user
    await n4bots.add_user(client, message)

    # Simple welcome animation
    m = await message.reply_text("ꜱᴛᴀʀᴛɪɴɢ...")
    await asyncio.sleep(0.5)
    await m.edit_text("⚡")
    await asyncio.sleep(0.6)
    await m.delete()
    
    # Define buttons for the start message
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs", callback_data='help')
        ],
        [
            InlineKeyboardButton('ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Animelibraryn4')
        ],
        [
            InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about'),
            InlineKeyboardButton('sᴏᴜʀᴄᴇ', callback_data='source')
        ]
    ])

    # Send start message with or without picture
    if Config.START_PIC:
        await message.reply_photo(
            Config.START_PIC,
            caption=Txt.START_TXT.format(user.mention),
            reply_markup=buttons
        )
    else:
        await message.reply_text(
            text=Txt.START_TXT.format(user.mention),
            reply_markup=buttons,
            disable_web_page_preview=True
        )

# Update the callback regex pattern to include mode-related callbacks:
@Client.on_callback_query(filters.regex(r'^(home|caption|help|meta|donate|file_names|thumbnail|metadatax|source|premiumx|plans|about|close|setmedia_|on_metadata|off_metadata|metainfo|back_to_welcome|premium_page|close_message|set_mode_|close_mode)$'))
async def cb_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    print(f"Callback data received: {data}")  # Debugging line

    # ADD BAN CHECK FOR CALLBACK QUERIES TOO
    # Check if user is banned when they click buttons
    if user_id != Config.ADMIN:  # Skip check for admin
        try:
            # Use the check_ban_status function from admin_panel
            from plugins.admin_panel import check_ban_status
            
            # Create a mock message object for check_ban_status
            class MockMessage:
                def __init__(self, user_id, chat_id):
                    self.from_user = type('obj', (object,), {'id': user_id})()
                    self.chat = type('obj', (object,), {'id': chat_id})()
            
            mock_msg = MockMessage(user_id, query.message.chat.id)
            is_banned = await check_ban_status(client, mock_msg)
            
            if is_banned:
                await query.answer("🚫 You are banned from using this bot.", show_alert=True)
                return
        except Exception as e:
            print(f"Error checking ban status in callback: {e}")

    if data == "home":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs", callback_data='help')],
                [InlineKeyboardButton('ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Animelibraryn4')],
                [InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about'), InlineKeyboardButton('sᴏᴜʀᴄᴇ', callback_data='source')]
            ])
        )
        
    elif data == "caption":
        await query.message.edit_text(
            text=Txt.CAPTION_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help")]
            ])
        )

    elif data == "help":
        # Ensure these lines have 4 spaces or 1 tab indentation
        bot = await client.get_me()
        mention = bot.mention if hasattr(bot, 'mention') else f"@{bot.username}"
        
        await query.message.edit_text(
            text=Txt.HELP_TXT.format(mention=mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ", callback_data='file_names')],
                [InlineKeyboardButton('ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='thumbnail'), InlineKeyboardButton('ᴄᴀᴘᴛɪᴏɴ', callback_data='caption')],
                [InlineKeyboardButton('ᴍᴇᴛᴀᴅᴀᴛᴀ', callback_data='meta'), InlineKeyboardButton('ᴅᴏɴᴀᴛᴇ', callback_data='donate')],
                [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='home')]
            ])
        )

    elif data == "meta":
        await query.message.edit_text(
            text=Txt.SEND_METADATA,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help")]
            ])
        )
    elif data == "donate":
        await query.message.edit_text(
            text=Txt.DONATE_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help"), InlineKeyboardButton("ᴏᴡɴᴇʀ", url='https://t.me/Anime_library_n4')]
            ])
        )
    elif data == "file_names":
        format_template = await n4bots.get_format_template(user_id)
        await query.message.edit_text(
            text=Txt.FILE_NAME_TXT.format(format_template=format_template),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help")]
            ])
        )
    elif data == "thumbnail":
        await query.message.edit_caption(
            caption=Txt.THUMBNAIL_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help")]
            ])
        )
    elif data == "metadatax":
        await query.message.edit_caption(
            caption=Txt.SEND_METADATA,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help")]
            ])
        )
    elif data == "source":
        await query.message.edit_caption(
            caption=Txt.SOURCE_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="home")]
            ])
        )
    elif data == "premiumx":
        await query.message.edit_caption(
            caption=Txt.PREMIUM_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="help"), InlineKeyboardButton("ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", url='https://t.me/Tanjiro_kamado_n4_bot')]
            ])
        )
    elif data == "plans":
        await query.message.edit_caption(
            caption=Txt.PREPLANS_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close"), InlineKeyboardButton("ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ", url='https://t.me/Tanjiro_kamado_n4_bot')]
            ])
        )
    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴄᴏᴍᴍᴀɴᴅs", callback_data="help"), InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", url='https://t.me/Tanjiro_kamado_n4_bot')],
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="home")]
            ])
        )
    elif data == "close":
        try:
            await query.message.delete()
            await query.message.reply_to_message.delete()
        except:
            await query.message.delete()
    
    # Metadata callbacks
    elif data in ["on_metadata", "off_metadata"]:
        # Handle metadata toggle here or let metadata.py handle it
        # Since metadata.py has its own handler, we'll just pass it through
        pass
        
    elif data == "metainfo":
        await query.message.edit_text(
            text=Txt.META_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Hᴏᴍᴇ", callback_data="home"),
                    InlineKeyboardButton("Bᴀᴄᴋ", callback_data="help")
                ]
            ])
        )
    
    # Verification callbacks
    elif data == "back_to_welcome":
        # Let __init__.py handle this
        pass
        
    elif data == "premium_page":
        # Let __init__.py handle this
        pass
        
    elif data == "close_message":
        # Let __init__.py handle this
        pass
    
    # Set media preference
    elif data.startswith("setmedia_"):
        user_id = query.from_user.id
        media_type = data.split("_", 1)[1]
        await n4bots.set_media_preference(user_id, media_type)
        await query.answer(f"Media preference set to: {media_type} ✅")
        await query.message.edit_text(f"**Media preference set to:** {media_type} ✅")


# Donation Command Handler - ADD BAN CHECK HERE TOO
@Client.on_message(filters.command("donate"))
async def donation(client, message):
    # Add ban check
    if message.from_user.id != Config.ADMIN:
        is_banned = await check_ban_status(client, message)
        if is_banned:
            return
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="help"), InlineKeyboardButton(text="ᴏᴡɴᴇʀ", url='https://t.me/Tanjiro_kamado_n4_bot')]
    ])
    yt = await message.reply_photo(photo='https://graph.org/file/1919fe077848bd0783d4c.jpg', caption=Txt.DONATE_TXT, reply_markup=buttons)
    await asyncio.sleep(300)
    await yt.delete()
    await message.delete()

# Bought Command Handler - ADD BAN CHECK HERE TOO
@Client.on_message(filters.command("bought") & filters.private)
async def bought(client, message):
    # Add ban check
    if message.from_user.id != Config.ADMIN:
        is_banned = await check_ban_status(client, message)
        if is_banned:
            return
    
    msg = await message.reply('Wait im checking...')
    replied = message.reply_to_message

    if not replied:
        await msg.edit("<b>Please reply with the screenshot of your payment for the premium purchase to proceed.\n\nFor example, first upload your screenshot, then reply to it using the '/bought' command</b>")
    elif replied.photo:
        await client.send_photo(
            chat_id=LOG_CHANNEL,
            photo=replied.photo.file_id,
            caption=f'<b>User - {message.from_user.mention}\nUser id - <code>{message.from_user.id}</code>\nUsername - <code>{message.from_user.username}</code>\nName - <code>{message.from_user.first_name}</code></b>',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Close", callback_data="close_data")]
            ])
        )
        await msg.edit_text('<b>Your screenshot has been sent to Admins</b>')

@Client.on_message(filters.private & filters.command("help"))
async def help_command(client, message):
    # ADD BAN CHECK
    is_banned = await check_ban_status(client, message)
    if is_banned:
        return
    
    # Get bot info properly
    bot = await client.get_me()
    mention = bot.mention if hasattr(bot, 'mention') else f"@{bot.username}"

    await message.reply_text(
        text=Txt.HELP_TXT.format(mention=mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ғᴏʀᴍᴀᴛ", callback_data='file_names')],
            [InlineKeyboardButton('ᴛʜᴜᴍʙɴᴀɪʟ', callback_data='thumbnail'), InlineKeyboardButton('ᴄᴀᴘᴛɪᴏɴ', callback_data='caption')],
            [InlineKeyboardButton('ᴍᴇᴛᴀᴅᴀᴛᴀ', callback_data='meta'), InlineKeyboardButton('ᴅᴏɴᴀᴛᴇ', callback_data='donate')],
            [InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='home')]
        ])
    )

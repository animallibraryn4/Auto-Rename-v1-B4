import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant
from helper.database import n4bots

# Default image URL (can be made dynamic later)
IMAGE_URL = "https://graph.org/file/a27d85469761da836337c.jpg"

async def get_force_sub_channels():
    """Get force sub channels dynamically from database"""
    try:
        bot_settings = await n4bots.get_bot_settings()
        if bot_settings and "force_sub_channels" in bot_settings:
            return bot_settings.get("force_sub_channels", ["animelibraryn4"])
        return ["animelibraryn4"]  # Default fallback
    except Exception as e:
        print(f"Error getting force sub channels: {e}")
        return ["animelibraryn4"]

async def not_subscribed(_, __, message):
    channels = await get_force_sub_channels()
    if not channels:  # If no channels, no force subscription required
        return False
        
    for channel in channels:
        try:
            user = await message._client.get_chat_member(channel, message.from_user.id)
            if user.status in {"kicked", "left"}:
                return True
        except UserNotParticipant:
            return True
    return False

@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    channels = await get_force_sub_channels()
    if not channels:  # If no channels, don't show force subscription
        return
        
    not_joined_channels = []
    for channel in channels:
        try:
            user = await client.get_chat_member(channel, message.from_user.id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel)
        except UserNotParticipant:
            not_joined_channels.append(channel)

    # If user has joined all channels, don't show the message
    if not not_joined_channels:
        return

    buttons = [
        [
            InlineKeyboardButton(
                text=f"Join {channel.capitalize()}", url=f"https://t.me/{channel}"
            )
        ]
        for channel in not_joined_channels
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="I have joined", callback_data="check_subscription"
            )
        ]
    )

    text = "** ЩбіАбіЛбіЛбіА!!,  ПбіПбіЬ' АбіЗ …ібіПбіЫ біКбіП…™…ібіЗбіЕ біЫбіП біА Я Я  АбіЗ«ЂбіЬ…™ АбіЗбіЕ біД ЬбіА…і…ібіЗ Яs, біКбіП…™…і біЫ ЬбіЗ біЬбіШбіЕбіАбіЫбіЗ біД ЬбіА…і…ібіЗ Яs біЫбіП біДбіП…ібіЫ…™…ібіЬбіЗ**"
    await message.reply_photo(
        photo=IMAGE_URL,
        caption=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("check_subscription"))
async def check_subscription(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    channels = await get_force_sub_channels()
    not_joined_channels = []

    for channel in channels:
        try:
            user = await client.get_chat_member(channel, user_id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel)
        except UserNotParticipant:
            not_joined_channels.append(channel)

    if not not_joined_channels:
        # User has joined all channels
        new_text = "** ПбіПбіЬ  ЬбіАбі†біЗ біКбіП…™…ібіЗбіЕ біА Я Я біЫ ЬбіЗ  АбіЗ«ЂбіЬ…™ АбіЗбіЕ біД ЬбіА…і…ібіЗ Яs. біЫ ЬбіА…ібіЛ  ПбіПбіЬ! рЯШК /start …ібіПбі°**"
        if callback_query.message.caption != new_text:
            await callback_query.message.edit_caption(
                caption=new_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("…ібіПбі° біД Я…™біДбіЛ  ЬбіЗ АбіЗ", callback_data='help')]
                ])
            )
    else:
        # User still hasn't joined some channels
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"Join {channel.capitalize()}",
                    url=f"https://t.me/{channel}",
                )
            ]
            for channel in not_joined_channels
        ]
        buttons.append(
            [
                InlineKeyboardButton(
                    text="I have joined", callback_data="check_subscription"
                )
            ]
        )
        
        text = "**ʏᴏᴜ ʜᴀᴠᴇ ᴊᴏɪɴᴇᴅ ᴀʟʟ ᴛʜᴇ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟs. ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴛʜᴇ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ**"
        if callback_query.message.caption != text:
            await callback_query.message.edit_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

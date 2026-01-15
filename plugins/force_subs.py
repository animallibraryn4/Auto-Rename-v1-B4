import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant
from config import Config, Txt

IMAGE_URL = "https://graph.org/file/a27d85469761da836337c.jpg"

# Get active force subscribe channels
FORCE_SUB_CHANNELS = Config.get_force_sub_channels()

async def not_subscribed(_, __, message):
    if not FORCE_SUB_CHANNELS:
        return False
        
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            user = await message._client.get_chat_member(channel_id, message.from_user.id)
            if user.status in {"kicked", "left"}:
                return True
        except UserNotParticipant:
            return True
        except Exception as e:
            print(f"Error checking channel {channel_id}: {e}")
            continue
    return False

@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    if not FORCE_SUB_CHANNELS:
        return
        
    not_joined_channels = []
    channel_info = {}
    
    # Get channel information
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            chat = await client.get_chat(channel_id)
            channel_name = chat.title or f"Channel {channel_id}"
            invite_link = chat.invite_link
            
            user = await client.get_chat_member(channel_id, message.from_user.id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append({
                    'id': channel_id,
                    'name': channel_name,
                    'invite_link': invite_link
                })
        except UserNotParticipant:
            not_joined_channels.append({
                'id': channel_id,
                'name': channel_name,
                'invite_link': invite_link
            })
        except Exception as e:
            print(f"Error getting chat info for {channel_id}: {e}")
            continue

    if not not_joined_channels:
        return
        
    # Create buttons for each channel
    buttons = []
    for channel in not_joined_channels:
        if channel['invite_link']:
            buttons.append([
                InlineKeyboardButton(
                    text=f"Join {channel['name']}",
                    url=channel['invite_link']
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    text=f"Join {channel['name']}",
                    url=f"https://t.me/{channel['id']}" if str(channel['id']).startswith('@') else f"https://t.me/c/{str(channel['id']).replace('-100', '')}"
                )
            ])
    
    buttons.append([
        InlineKeyboardButton(
            text="I have joined",
            callback_data="check_subscription"
        )
    ])

    text = """**Please join our channels to use this bot!**

<blockquote expandable><b>Steps:</b>
1. Join the channels below
2. Come back and click "I Have Joined"
3. Start using the bot!<blockquote>

<b>Note:</b> You need to join all the required channels.
"""

    # Send the force subscribe message
    await message.reply_photo(
        photo=IMAGE_URL,
        caption=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^check_subscription$"))
async def check_subscription(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    if not FORCE_SUB_CHANNELS:
        await callback_query.message.delete()
        await send_start_message(client, callback_query)
        return
        
    not_joined_channels = []
    
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            user = await client.get_chat_member(channel_id, user_id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel_id)
        except UserNotParticipant:
            not_joined_channels.append(channel_id)
        except Exception as e:
            print(f"Error checking subscription for {channel_id}: {e}")
            continue

    if not not_joined_channels:
        # User has joined all channels
        await callback_query.message.delete()
        await send_start_message(client, callback_query)
    else:
        # User hasn't joined all channels
        await callback_query.answer("❌ Please join all channels first!", show_alert=True)
        
        # Update the message with remaining channels
        channel_info = {}
        for channel_id in not_joined_channels:
            try:
                chat = await client.get_chat(channel_id)
                channel_info[channel_id] = {
                    'name': chat.title or f"Channel {channel_id}",
                    'invite_link': chat.invite_link
                }
            except Exception as e:
                channel_info[channel_id] = {
                    'name': f"Channel {channel_id}",
                    'invite_link': None
                }

        # Create new buttons
        buttons = []
        for channel_id in not_joined_channels:
            info = channel_info.get(channel_id, {})
            if info.get('invite_link'):
                buttons.append([
                    InlineKeyboardButton(
                        text=f"📢 Join {info['name']}",
                        url=info['invite_link']
                    )
                ])
            else:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"📢 Join {info['name']}",
                        url=f"https://t.me/{channel_id}" if str(channel_id).startswith('@') else f"https://t.me/c/{str(channel_id).replace('-100', '')}"
                    )
                ])
        
        buttons.append([
            InlineKeyboardButton(
                text="✅ I have joined",
                callback_data="check_subscription"
            )
        ])

        text = f"""**❌ You still need to join {len(not_joined_channels)} channel(s)!**

Please join all the channels below:"""

        try:
            await callback_query.message.edit_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except Exception as e:
            print(f"Error editing message: {e}")
            await callback_query.answer("Please try again!", show_alert=True)

async def send_start_message(client, callback_query: CallbackQuery):
    """Send the normal /start command message"""
    user = callback_query.from_user
    
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
        await client.send_photo(
            chat_id=user.id,
            photo=Config.START_PIC,
            caption=Txt.START_TXT.format(user.mention),
            reply_markup=buttons
        )
    else:
        await client.send_message(
            chat_id=user.id,
            text=Txt.START_TXT.format(user.mention),
            reply_markup=buttons,
            disable_web_page_preview=True
        )

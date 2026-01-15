import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant
from config import Config

FORCE_SUB_CHANNELS = Config.FORCE_SUB_CHANNELS
IMAGE_URL = "https://graph.org/file/a27d85469761da836337c.jpg"

async def not_subscribed(_, __, message):
    for channel in FORCE_SUB_CHANNELS:
        try:
            user = await message._client.get_chat_member(int(channel), message.from_user.id)
            if user.status in {"kicked", "left"}:
                return True
        except UserNotParticipant:
            return True
        except Exception as e:
            print(f"Error checking subscription for channel {channel}: {e}")
            return True
    return False

@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    not_joined_channels = []
    channel_info = {}
    
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            chat = await client.get_chat(int(channel_id))
            channel_name = chat.title if chat.title else f"Channel {channel_id}"
            invite_link = chat.invite_link if chat.invite_link else None
            
            user = await client.get_chat_member(int(channel_id), message.from_user.id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append({
                    'id': channel_id,
                    'name': channel_name,
                    'invite_link': invite_link
                })
        except UserNotParticipant:
            not_joined_channels.append({
                'id': channel_id,
                'name': f"Channel {channel_id}",
                'invite_link': None
            })
        except Exception as e:
            print(f"Error getting channel info for {channel_id}: {e}")
            continue

    if not not_joined_channels:
        return

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
                    url=f"https://t.me/c/{str(channel['id'])[4:]}"
                )
            ])
    
    buttons.append([
        InlineKeyboardButton(
            text="✅ I have joined", 
            callback_data="check_subscription"
        )
    ])

    text = "**Please join all the channels below to use this bot. After joining, click 'I have joined'**"
    await message.reply_photo(
        photo=IMAGE_URL,
        caption=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("check_subscription"))
async def check_subscription(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    not_joined_channels = []
    
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            user = await client.get_chat_member(int(channel_id), user_id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel_id)
        except UserNotParticipant:
            not_joined_channels.append(channel_id)
        except Exception as e:
            print(f"Error checking subscription for channel {channel_id}: {e}")
            not_joined_channels.append(channel_id)

    if not not_joined_channels:
        # Delete the force sub message
        try:
            await callback_query.message.delete()
        except:
            pass
        
        # Send the normal start message
        from config import Txt
        user = callback_query.from_user
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs", callback_data='help')],
            [InlineKeyboardButton('ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Animelibraryn4')],
            [
                InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about'),
                InlineKeyboardButton('sᴏᴜʀᴄᴇ', callback_data='source')
            ]
        ])
        
        if Config.START_PIC:
            await callback_query.message.reply_photo(
                Config.START_PIC,
                caption=Txt.START_TXT.format(user.mention),
                reply_markup=buttons
            )
        else:
            await callback_query.message.reply_text(
                text=Txt.START_TXT.format(user.mention),
                reply_markup=buttons,
                disable_web_page_preview=True
            )
        
        await callback_query.answer("✅ Successfully verified! Welcome to the bot!", show_alert=True)
    else:
        # Get updated channel info
        buttons = []
        for channel_id in not_joined_channels:
            try:
                chat = await client.get_chat(int(channel_id))
                channel_name = chat.title if chat.title else f"Channel {channel_id}"
                invite_link = chat.invite_link if chat.invite_link else None
                
                if invite_link:
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"Join {channel_name}",
                            url=invite_link
                        )
                    ])
                else:
                    buttons.append([
                        InlineKeyboardButton(
                            text=f"Join {channel_name}",
                            url=f"https://t.me/c/{str(channel_id)[4:]}"
                        )
                    ])
            except Exception as e:
                print(f"Error getting channel info: {e}")
                continue
        
        buttons.append([
            InlineKeyboardButton(
                text="✅ I have joined", 
                callback_data="check_subscription"
            )
        ])
        
        text = "**Please join all the channels below to use this bot. After joining, click 'I have joined'**"
        try:
            await callback_query.message.edit_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await callback_query.answer("❌ Please join all channels first!", show_alert=True)
        except Exception as e:
            print(f"Error editing message: {e}")
            await callback_query.answer("❌ Please join all channels first!", show_alert=True)

import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
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
    
    for channel_id in FORCE_SUB_CHANNELS:
        try:
            # Try to get user status in channel
            try:
                user = await client.get_chat_member(int(channel_id), message.from_user.id)
                if user.status in {"kicked", "left"}:
                    not_joined_channels.append(channel_id)
            except UserNotParticipant:
                not_joined_channels.append(channel_id)
            except Exception as e:
                print(f"Error checking user status in channel {channel_id}: {e}")
                not_joined_channels.append(channel_id)
                
        except Exception as e:
            print(f"Error with channel {channel_id}: {e}")
            not_joined_channels.append(channel_id)

    if not not_joined_channels:
        return

    # Build buttons for channels
    buttons = []
    for channel_id in not_joined_channels:
        try:
            # Get channel info
            chat = await client.get_chat(int(channel_id))
            channel_name = chat.title if chat.title else f"Channel {channel_id}"
            
            # Try to get invite link
            try:
                invite_link = await client.export_chat_invite_link(int(channel_id))
            except:
                # If bot doesn't have permission to create invite link, use alternative
                invite_link = f"https://t.me/c/{str(channel_id)[4:]}"
                
            buttons.append([
                InlineKeyboardButton(
                    text=f"Join {channel_name}",
                    url=invite_link
                )
            ])
        except Exception as e:
            print(f"Error getting info for channel {channel_id}: {e}")
            # Fallback button
            buttons.append([
                InlineKeyboardButton(
                    text=f"Join Channel {channel_id}",
                    url=f"https://t.me/c/{str(channel_id)[4:]}"
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
        from config import Txt, Config
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
                
                try:
                    invite_link = await client.export_chat_invite_link(int(channel_id))
                except:
                    invite_link = f"https://t.me/c/{str(channel_id)[4:]}"
                
                buttons.append([
                    InlineKeyboardButton(
                        text=f"Join {channel_name}",
                        url=invite_link
                    )
                ])
            except Exception as e:
                print(f"Error getting channel info: {e}")
                buttons.append([
                    InlineKeyboardButton(
                        text=f"Join Channel {channel_id}",
                        url=f"https://t.me/c/{str(channel_id)[4:]}"
                    )
                ])
        
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

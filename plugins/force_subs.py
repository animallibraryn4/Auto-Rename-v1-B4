import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant
from config import Config, Txt
from helper.database import n4bots

FORCE_SUB_CHANNELS = Config.FORCE_SUB_CHANNELS
MAX_CHANNELS = 5  # Maximum 5 force subscribe channels

async def not_subscribed(_, __, message):
    if not FORCE_SUB_CHANNELS:
        return False
        
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            user = await message._client.get_chat_member(channel_id, message.from_user.id)
            if user.status in {"kicked", "left"}:
                return True
        except UserNotParticipant:
            return True
        except Exception as e:
            print(f"Error checking subscription: {e}")
            continue
    return False

@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    if not FORCE_SUB_CHANNELS:
        return
        
    not_joined_channels = []
    
    # Check each channel (up to MAX_CHANNELS)
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            user = await client.get_chat_member(channel_id, message.from_user.id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel_id)
        except UserNotParticipant:
            not_joined_channels.append(channel_id)
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    if not not_joined_channels:
        return
    
    # Create buttons for each channel
    buttons = []
    
    for channel_id in not_joined_channels:
        try:
            chat = await client.get_chat(channel_id)
            channel_name = chat.title if hasattr(chat, 'title') else f"Channel {channel_id}"
            # Try to get invite link
            try:
                invite_link = await client.export_chat_invite_link(channel_id)
            except:
                # If bot can't export invite link, use t.me format
                if chat.username:
                    invite_link = f"https://t.me/{chat.username}"
                else:
                    invite_link = f"https://t.me/c/{str(channel_id).replace('-100', '')}"
            
            buttons.append([
                InlineKeyboardButton(
                    text=f"Join {channel_name}",
                    url=invite_link
                )
            ])
        except Exception as e:
            print(f"Error getting channel info: {e}")
            continue
    
    buttons.append([
        InlineKeyboardButton(
            text="✅ I Have Joined",
            callback_data="check_subscription"
        )
    ])
    
    text = """**Please Join Our Channel(s) First!**\n\nAfter joining, click the **"I Have Joined"** button below."""
    
    await message.reply_photo(
        photo="https://graph.org/file/a27d85469761da836337c.jpg",
        caption=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("check_subscription"))
async def check_subscription(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    not_joined_channels = []
    
    if not FORCE_SUB_CHANNELS:
        await callback_query.message.delete()
        # Send start message
        from start import send_start_message
        await send_start_message(client, callback_query.message)
        return
    
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            user = await client.get_chat_member(channel_id, user_id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel_id)
        except UserNotParticipant:
            not_joined_channels.append(channel_id)
        except Exception as e:
            print(f"Error checking subscription: {e}")
            continue
    
    if not not_joined_channels:
        # User has joined all channels - DELETE the prompt and send start message
        await callback_query.message.delete()
        
        # Import and call send_start_message function
        from start import send_start_message
        await send_start_message(client, callback_query.message)
        await callback_query.answer("✅ All channels joined! Welcome!", show_alert=True)
    else:
        # Update with remaining channels
        buttons = []
        
        for channel_id in not_joined_channels:
            try:
                chat = await client.get_chat(channel_id)
                channel_name = chat.title if hasattr(chat, 'title') else f"Channel {channel_id}"
                # Try to get invite link
                try:
                    invite_link = await client.export_chat_invite_link(channel_id)
                except:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                    else:
                        invite_link = f"https://t.me/c/{str(channel_id).replace('-100', '')}"
                
                buttons.append([
                    InlineKeyboardButton(
                        text=f"Join {channel_name}",
                        url=invite_link
                    )
                ])
            except Exception as e:
                print(f"Error getting channel info: {e}")
                continue
        
        buttons.append([
            InlineKeyboardButton(
                text="✅ I Have Joined",
                callback_data="check_subscription"
            )
        ])
        
        text = f"""**Please Join All Channel(s) First!**\n\nYou still need to join {len(not_joined_channels)} channel(s).\nAfter joining, click the **"I Have Joined"** button again."""
        
        await callback_query.message.edit_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await callback_query.answer(f"Please join all {len(not_joined_channels)} channel(s) first!", show_alert=True)

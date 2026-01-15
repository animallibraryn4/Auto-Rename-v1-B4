import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from config import Config, Txt
import asyncio

FORCE_SUB_CHANNELS = Config.FORCE_SUB_CHANNELS
MAX_CHANNELS = 5  # Maximum 5 force subscribe channels

async def not_subscribed(_, client, message):
    """Check if user is not subscribed to any of the force channels"""
    if not FORCE_SUB_CHANNELS or len(FORCE_SUB_CHANNELS) == 0:
        return False
    
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            # Get chat member status
            user = await client.get_chat_member(channel_id, message.from_user.id)
            if user.status in ["kicked", "left", "restricted"]:
                return True
        except UserNotParticipant:
            return True
        except Exception as e:
            print(f"Error checking subscription for channel {channel_id}: {e}")
            continue
    return False

@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    """Handle force subscription prompt"""
    user = message.from_user
    
    # Check which channels user hasn't joined
    not_joined_channels = []
    channel_info = []  # Store (channel_id, channel_name, invite_link)
    
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            user_status = await client.get_chat_member(channel_id, user.id)
            if user_status.status in ["kicked", "left", "restricted"]:
                not_joined_channels.append(channel_id)
        except UserNotParticipant:
            not_joined_channels.append(channel_id)
        except Exception as e:
            print(f"Error checking channel {channel_id}: {e}")
    
    if not not_joined_channels:
        return  # User is subscribed to all channels
    
    # Get channel info and invite links
    buttons = []
    for channel_id in not_joined_channels:
        try:
            chat = await client.get_chat(channel_id)
            channel_name = chat.title or f"Channel {channel_id}"
            
            # Try to get invite link
            invite_link = None
            try:
                if chat.username:
                    invite_link = f"https://t.me/{chat.username}"
                else:
                    # Try to create invite link if bot is admin
                    invite_link = await client.export_chat_invite_link(channel_id)
            except (ChatAdminRequired, Exception):
                # If can't create invite link, use the t.me format for private channels
                if str(channel_id).startswith("-100"):
                    invite_link = f"https://t.me/c/{str(channel_id).replace('-100', '')}"
                else:
                    invite_link = f"https://t.me/c/{channel_id}"
            
            if invite_link:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"📢 Join {channel_name}",
                        url=invite_link
                    )
                ])
                channel_info.append((channel_id, channel_name, invite_link))
                
        except Exception as e:
            print(f"Error getting info for channel {channel_id}: {e}")
            continue
    
    if not buttons:  # No valid channels to show
        return
    
    # Add verify button
    buttons.append([
        InlineKeyboardButton(
            text="✅ I Have Joined",
            callback_data="check_subscription"
        )
    ])
    
    caption = f"""**👋 Hello {user.first_name}!**

Please join our channel(s) to use this bot.

**Steps:**
1. Join the channel(s) below
2. Come back and click **"I Have Joined"**
3. Start using the bot!

**Note:** You need to join **all** the required channels."""
    
    # Send or update message
    if message.text == "/start":
        # If it's a start command, send new message
        await message.reply_photo(
            photo="https://graph.org/file/a27d85469761da836337c.jpg",
            caption=caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # For other messages, reply
        await message.reply_photo(
            photo="https://graph.org/file/a27d85469761da836337c.jpg",
            caption=caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@Client.on_callback_query(filters.regex("^check_subscription$"))
async def check_subscription(client, callback_query: CallbackQuery):
    """Verify user subscription and delete prompt"""
    user = callback_query.from_user
    user_id = user.id
    
    # Check if user has joined all channels
    not_joined_channels = []
    
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            user_status = await client.get_chat_member(channel_id, user_id)
            if user_status.status in ["kicked", "left", "restricted"]:
                not_joined_channels.append(channel_id)
        except UserNotParticipant:
            not_joined_channels.append(channel_id)
        except Exception as e:
            print(f"Error checking channel {channel_id}: {e}")
            not_joined_channels.append(channel_id)
    
    if not_joined_channels:
        # User hasn't joined all channels
        remaining_channels = []
        for channel_id in not_joined_channels:
            try:
                chat = await client.get_chat(channel_id)
                channel_name = chat.title or f"Channel {channel_id}"
                
                # Get invite link
                invite_link = None
                try:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
                    else:
                        invite_link = await client.export_chat_invite_link(channel_id)
                except:
                    if str(channel_id).startswith("-100"):
                        invite_link = f"https://t.me/c/{str(channel_id).replace('-100', '')}"
                    else:
                        invite_link = f"https://t.me/c/{channel_id}"
                
                if invite_link:
                    remaining_channels.append((channel_name, invite_link))
            except:
                continue
        
        # Create new buttons for remaining channels
        buttons = []
        for channel_name, invite_link in remaining_channels:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📢 Join {channel_name}",
                    url=invite_link
                )
            ])
        
        buttons.append([
            InlineKeyboardButton(
                text="✅ I Have Joined",
                callback_data="check_subscription"
            )
        ])
        
        caption = f"""**⚠️ Please join all channels!**

You still need to join {len(remaining_channels)} channel(s):

**Instructions:**
1. Join the remaining channel(s) above
2. Come back and click **"I Have Joined"** again
3. You must join **all** channels to proceed"""
        
        try:
            await callback_query.message.edit_caption(
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await callback_query.answer(f"Please join {len(remaining_channels)} more channel(s)!", show_alert=True)
        except:
            await callback_query.answer("Please join all channels first!", show_alert=True)
        
        return
    
    # User has joined all channels
    try:
        # Delete the force subscribe message
        await callback_query.message.delete()
        
        # Send welcome animation
        welcome_msg = await client.send_message(
            user_id,
            "🎉 **Welcome!** 🎉\n\n**Verification successful!**\n\nStarting bot..."
        )
        await asyncio.sleep(1)
        
        # Send the start message
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs", callback_data='help')],
            [InlineKeyboardButton('ᴜᴘᴅᴀᴛᴇs', url='https://t.me/Animelibraryn4')],
            [
                InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data='about'),
                InlineKeyboardButton('sᴏᴜʀᴄᴇ', callback_data='source')
            ]
        ])
        
        if Config.START_PIC:
            await client.send_photo(
                chat_id=user_id,
                photo=Config.START_PIC,
                caption=Txt.START_TXT.format(user.mention),
                reply_markup=buttons
            )
        else:
            await client.send_message(
                chat_id=user_id,
                text=Txt.START_TXT.format(user.mention),
                reply_markup=buttons,
                disable_web_page_preview=True
            )
        
        # Delete the welcome animation
        try:
            await welcome_msg.delete()
        except:
            pass
            
        await callback_query.answer("✅ Verification successful! Welcome!", show_alert=False)
        
    except Exception as e:
        print(f"Error in check_subscription: {e}")
        await callback_query.answer("Error occurred. Please try /start again.", show_alert=True)

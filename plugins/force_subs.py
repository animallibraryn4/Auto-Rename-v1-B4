import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelInvalid, ChannelPrivate, PeerIdInvalid
from config import Config, Txt

FORCE_SUB_CHANNELS = Config.FORCE_SUB_CHANNELS
MAX_CHANNELS = 5

print(f"FORCE_SUB_DEBUG: Loaded {len(FORCE_SUB_CHANNELS)} channels: {FORCE_SUB_CHANNELS}")

async def is_user_subscribed(client, user_id, channel_id):
    """Check if a user is subscribed to a channel"""
    try:
        # First, check if bot can access the channel
        try:
            chat = await client.get_chat(channel_id)
            print(f"FORCE_SUB_DEBUG: Bot can access channel {channel_id} ({chat.title})")
        except Exception as e:
            print(f"FORCE_SUB_DEBUG: Bot cannot access channel {channel_id}: {e}")
            return True  # If bot can't access, skip this channel
        
        # Check user membership
        try:
            user = await client.get_chat_member(channel_id, user_id)
            print(f"FORCE_SUB_DEBUG: User {user_id} status in {channel_id}: {user.status}")
            
            if user.status in ["kicked", "left"]:
                return False
            return True
        except UserNotParticipant:
            print(f"FORCE_SUB_DEBUG: User {user_id} not participant in {channel_id}")
            return False
        except Exception as e:
            print(f"FORCE_SUB_DEBUG: Error checking user {user_id} in {channel_id}: {e}")
            return True  # Skip on error
        
    except Exception as e:
        print(f"FORCE_SUB_DEBUG: General error for channel {channel_id}: {e}")
        return True  # Skip on error

async def not_subscribed(_, client, message):
    """Check if user is not subscribed to any channel"""
    if not FORCE_SUB_CHANNELS or len(FORCE_SUB_CHANNELS) == 0:
        print("FORCE_SUB_DEBUG: No channels configured")
        return False
    
    user_id = message.from_user.id
    
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            # Try to get chat info first to verify bot access
            try:
                chat = await client.get_chat(channel_id)
                print(f"FORCE_SUB_DEBUG: Checking channel {channel_id} ({chat.title}) for user {user_id}")
            except Exception as e:
                print(f"FORCE_SUB_DEBUG: Skipping channel {channel_id}, bot can't access: {e}")
                continue  # Skip channels bot can't access
            
            # Check user subscription
            try:
                user = await client.get_chat_member(channel_id, user_id)
                if user.status in ["kicked", "left"]:
                    print(f"FORCE_SUB_DEBUG: User {user_id} not in channel {channel_id}")
                    return True
            except UserNotParticipant:
                print(f"FORCE_SUB_DEBUG: User {user_id} not participant in {channel_id}")
                return True
            except Exception as e:
                print(f"FORCE_SUB_DEBUG: Error in get_chat_member for {channel_id}: {e}")
                continue
                
        except Exception as e:
            print(f"FORCE_SUB_DEBUG: Unexpected error for channel {channel_id}: {e}")
            continue
    
    print(f"FORCE_SUB_DEBUG: User {user_id} is subscribed to all channels")
    return False

@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    """Show force subscribe message"""
    user = message.from_user
    print(f"FORCE_SUB_DEBUG: Showing force sub for user {user.id}")
    
    # Get accessible channels
    accessible_channels = []
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            chat = await client.get_chat(channel_id)
            accessible_channels.append((channel_id, chat))
            print(f"FORCE_SUB_DEBUG: Channel accessible: {channel_id} - {chat.title}")
        except Exception as e:
            print(f"FORCE_SUB_DEBUG: Channel {channel_id} not accessible: {e}")
            continue
    
    if not accessible_channels:
        print("FORCE_SUB_DEBUG: No accessible channels, allowing user")
        return
    
    # Check which channels user needs to join
    need_to_join = []
    for channel_id, chat in accessible_channels:
        try:
            user_status = await client.get_chat_member(channel_id, user.id)
            if user_status.status in ["kicked", "left"]:
                need_to_join.append((channel_id, chat))
        except UserNotParticipant:
            need_to_join.append((channel_id, chat))
        except Exception as e:
            print(f"FORCE_SUB_DEBUG: Error checking user in {channel_id}: {e}")
            need_to_join.append((channel_id, chat))
    
    if not need_to_join:
        print(f"FORCE_SUB_DEBUG: User {user.id} already joined all channels")
        return
    
    # Create buttons
    buttons = []
    for channel_id, chat in need_to_join:
        channel_name = chat.title or f"Channel {abs(channel_id)}"
        
        # Get invite link
        invite_link = None
        try:
            if hasattr(chat, 'username') and chat.username:
                invite_link = f"https://t.me/{chat.username}"
            else:
                # Try to get invite link
                try:
                    invite_link = await client.export_chat_invite_link(channel_id)
                except:
                    # Fallback to t.me/c/ format
                    if str(channel_id).startswith("-100"):
                        invite_link = f"https://t.me/c/{str(abs(channel_id))}"
        except Exception as e:
            print(f"FORCE_SUB_DEBUG: Error getting invite link for {channel_id}: {e}")
            continue
        
        if invite_link:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📢 Join {channel_name}",
                    url=invite_link
                )
            ])
    
    if not buttons:
        print("FORCE_SUB_DEBUG: No valid buttons to show")
        return
    
    buttons.append([
        InlineKeyboardButton("✅ I Have Joined", callback_data="check_subscription")
    ])
    
    caption = f"""**👋 Hello {user.first_name}!**

📌 **Please join our channel(s) to use this bot.**

**Steps:**
1. Join the channel(s) below
2. Come back and click **"I Have Joined"**
3. Start using the bot!

**Note:** You need to join **all** the required channels."""
    
    try:
        await message.reply_photo(
            photo="https://graph.org/file/a27d85469761da836337c.jpg",
            caption=caption,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        print(f"FORCE_SUB_DEBUG: Force sub message sent to user {user.id}")
    except Exception as e:
        print(f"FORCE_SUB_DEBUG: Error sending force sub message: {e}")

@Client.on_callback_query(filters.regex("^check_subscription$"))
async def check_subscription(client, callback_query: CallbackQuery):
    """Handle subscription check"""
    user = callback_query.from_user
    user_id = user.id
    
    print(f"FORCE_SUB_DEBUG: Checking subscription for user {user_id}")
    
    # Get accessible channels
    accessible_channels = []
    for channel_id in FORCE_SUB_CHANNELS[:MAX_CHANNELS]:
        try:
            chat = await client.get_chat(channel_id)
            accessible_channels.append((channel_id, chat))
        except Exception as e:
            print(f"FORCE_SUB_DEBUG: Channel {channel_id} not accessible: {e}")
            continue
    
    if not accessible_channels:
        # No accessible channels, allow user
        await callback_query.message.delete()
        await send_welcome_message(client, user_id)
        return
    
    # Check user subscription
    need_to_join = []
    for channel_id, chat in accessible_channels:
        try:
            user_status = await client.get_chat_member(channel_id, user_id)
            if user_status.status in ["kicked", "left"]:
                need_to_join.append((channel_id, chat))
        except UserNotParticipant:
            need_to_join.append((channel_id, chat))
        except Exception as e:
            print(f"FORCE_SUB_DEBUG: Error checking {channel_id}: {e}")
            need_to_join.append((channel_id, chat))
    
    if need_to_join:
        # User needs to join more channels
        buttons = []
        for channel_id, chat in need_to_join:
            channel_name = chat.title or f"Channel {abs(channel_id)}"
            
            # Get invite link
            invite_link = None
            try:
                if hasattr(chat, 'username') and chat.username:
                    invite_link = f"https://t.me/{chat.username}"
                else:
                    try:
                        invite_link = await client.export_chat_invite_link(channel_id)
                    except:
                        if str(channel_id).startswith("-100"):
                            invite_link = f"https://t.me/c/{str(abs(channel_id))}"
            except:
                continue
            
            if invite_link:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"📢 Join {channel_name}",
                        url=invite_link
                    )
                ])
        
        if buttons:
            buttons.append([
                InlineKeyboardButton("✅ I Have Joined", callback_data="check_subscription")
            ])
            
            caption = f"""**⚠️ Please join all channels!**

You still need to join {len(need_to_join)} channel(s)."""
            
            try:
                await callback_query.message.edit_caption(
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                await callback_query.answer(f"Please join {len(need_to_join)} more channel(s)!", show_alert=True)
            except:
                await callback_query.answer("Please join all channels first!", show_alert=True)
        else:
            await callback_query.answer("Cannot verify channels. Please contact admin.", show_alert=True)
    else:
        # User has joined all channels
        await callback_query.message.delete()
        await send_welcome_message(client, user_id)

async def send_welcome_message(client, user_id):
    """Send welcome/start message after verification"""
    try:
        # Send welcome animation
        welcome_msg = await client.send_message(
            user_id,
            "✅ **Verification successful!**\n\nWelcome to the bot!"
        )
        await asyncio.sleep(1)
        
        # Send start message
        user = await client.get_users(user_id)
        
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
        
        # Delete welcome message
        try:
            await welcome_msg.delete()
        except:
            pass
            
        print(f"FORCE_SUB_DEBUG: Welcome message sent to user {user_id}")
        
    except Exception as e:
        print(f"FORCE_SUB_DEBUG: Error sending welcome message: {e}")

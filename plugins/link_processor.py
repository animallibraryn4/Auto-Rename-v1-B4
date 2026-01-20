

import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, ChannelPrivate, ChatAdminRequired
from helper.database import n4bots
from plugins.admin_panel import check_ban_status
from plugins import is_user_verified, send_verification

# Global state to track link processing
user_link_state = {}  # user_id -> processing state

async def extract_link_info(link: str):
    """
    Extract chat_id and message_id from Telegram message link
    Supports multiple formats:
    1. https://t.me/c/chat_id/message_id (private channels)
    2. https://t.me/username/message_id (public channels/groups)
    3. https://t.me/username/message_id?single (with parameters)
    """
    try:
        link = link.strip()
        
        # Remove any query parameters
        if '?' in link:
            link = link.split('?')[0]
        
        # Pattern for private channel links: /c/chat_id/message_id
        private_pattern = r't\.me/c/(\d+)/(\d+)'
        private_match = re.search(private_pattern, link)
        
        if private_match:
            chat_id_str = private_match.group(1)
            message_id = int(private_match.group(2))
            
            # Convert to proper negative chat_id
            if chat_id_str.startswith('-100'):
                chat_id = int(chat_id_str)
            elif chat_id_str.startswith('100'):
                chat_id = int('-' + chat_id_str)
            else:
                chat_id = int('-100' + chat_id_str)
            
            return {'type': 'private', 'chat_id': chat_id, 'message_id': message_id}
        
        # Pattern for public links: /username/message_id
        public_pattern = r't\.me/([a-zA-Z0-9_]+)/(\d+)'
        public_match = re.search(public_pattern, link)
        
        if public_match:
            username = public_match.group(1)
            message_id = int(public_match.group(2))
            
            # Check if it's a username (starts with letter) or numeric ID
            if username.isdigit():
                # It's actually a numeric ID
                if username.startswith('100'):
                    chat_id = int('-' + username)
                else:
                    chat_id = int('-100' + username)
                return {'type': 'private', 'chat_id': chat_id, 'message_id': message_id}
            else:
                # It's a username
                return {'type': 'public', 'username': username, 'message_id': message_id}
        
        return None
        
    except Exception as e:
        print(f"Error parsing link {link}: {e}")
        return None

async def process_single_link(client: Client, message: Message, link_info: dict):
    """Process a single Telegram file link"""
    user_id = message.from_user.id
    
    # Get user's current settings
    user_mode = await n4bots.get_mode(user_id)
    format_template = await n4bots.get_format_template(user_id)
    media_preference = await n4bots.get_media_preference(user_id)
    
    if not format_template:
        await message.reply_text(
            "⚠️ **Please set an auto-rename format first!**\n\n"
            "Use `/autorename` followed by your desired format.\n"
            "Example: `/autorename Naruto S[SE.NUM] E[EP.NUM] [QUALITY]`"
        )
        return
    
    # Check if user is in info mode
    from plugins.auto_rename import info_mode_users
    if user_id in info_mode_users:
        await message.reply_text("❌ **Cannot process links in Info Mode.**\nPlease exit Info Mode first.")
        return
    
    # Check if user is in sequence mode
    from plugins.sequence import user_sequences
    if user_id in user_sequences:
        await message.reply_text("❌ **Cannot process links in Sequence Mode.**\nPlease finish or cancel your sequence first.")
        return
    
    processing_msg = await message.reply_text("🔗 **Processing link...**")
    
    try:
        # Fetch the message
        if link_info['type'] == 'private':
            target_msg = await client.get_messages(
                chat_id=link_info['chat_id'],
                message_ids=link_info['message_id']
            )
        else:  # public
            target_msg = await client.get_messages(
                chat_id=link_info['username'],
                message_ids=link_info['message_id']
            )
        
        if not target_msg:
            await processing_msg.edit_text("❌ **Message not found!**\nThe link might be invalid or the message was deleted.")
            return
        
        # Check if it's a file
        if not (target_msg.document or target_msg.video or target_msg.audio):
            await processing_msg.edit_text("❌ **No file found in this message!**\nPlease provide a link to a file (document, video, or audio).")
            return
        
        await processing_msg.edit_text("✅ **Link processed!**\nProcessing file with auto-rename...")
        
        # Import the auto-rename handler
        from plugins.file_rename import auto_rename_files
        
        # Process the file through auto-rename system
        # We need to simulate a message from the user with the fetched message
        # Create a mock message object with the user's ID
        class MockMessage:
            def __init__(self, original_msg, target_msg):
                self.from_user = original_msg.from_user
                self.chat = original_msg.chat
                self.id = target_msg.id
                self.document = target_msg.document
                self.video = target_msg.video
                self.audio = target_msg.audio
                self.caption = target_msg.caption
                self.reply_to_message = None
        
        mock_message = MockMessage(message, target_msg)
        await auto_rename_files(client, mock_message)
        
        await processing_msg.delete()
        
    except ChannelPrivate:
        await processing_msg.edit_text(
            "❌ **Cannot access private channel!**\n\n"
            "The bot must be a member of the private channel to access files.\n"
            "Add @animelibraryn4 to the channel and grant appropriate permissions."
        )
    except ChatAdminRequired:
        await processing_msg.edit_text(
            "❌ **Admin permissions required!**\n\n"
            "For private channels, the bot needs admin rights to access messages.\n"
            "Please add the bot as an administrator in the channel."
        )
    except Exception as e:
        print(f"Error processing link: {e}")
        await processing_msg.edit_text(f"❌ **Error processing link:**\n`{str(e)[:200]}`")

async def process_multiple_links(client: Client, message: Message, links: list):
    """Process multiple Telegram file links"""
    user_id = message.from_user.id
    
    # Get user's current settings
    format_template = await n4bots.get_format_template(user_id)
    
    if not format_template:
        await message.reply_text(
            "⚠️ **Please set an auto-rename format first!**\n\n"
            "Use `/autorename` followed by your desired format."
        )
        return
    
    processing_msg = await message.reply_text(f"🔗 **Processing {len(links)} links...**\n\n0/{len(links)} completed")
    
    successful = 0
    failed = 0
    failed_list = []
    
    for i, link in enumerate(links, 1):
        try:
            link_info = await extract_link_info(link)
            if not link_info:
                failed += 1
                failed_list.append(f"{link} - Invalid format")
                continue
            
            # Update progress
            await processing_msg.edit_text(
                f"🔗 **Processing {len(links)} links...**\n\n"
                f"{i}/{len(links)} completed\n"
                f"✅ Successful: {successful}\n"
                f"❌ Failed: {failed}"
            )
            
            # Fetch and process the message
            if link_info['type'] == 'private':
                target_msg = await client.get_messages(
                    chat_id=link_info['chat_id'],
                    message_ids=link_info['message_id']
                )
            else:
                target_msg = await client.get_messages(
                    chat_id=link_info['username'],
                    message_ids=link_info['message_id']
                )
            
            if target_msg and (target_msg.document or target_msg.video or target_msg.audio):
                # Import the auto-rename handler
                from plugins.file_rename import auto_rename_files
                
                # Create a mock message object
                class MockMessage:
                    def __init__(self, original_msg, target_msg):
                        self.from_user = original_msg.from_user
                        self.chat = original_msg.chat
                        self.id = target_msg.id
                        self.document = target_msg.document
                        self.video = target_msg.video
                        self.audio = target_msg.audio
                        self.caption = target_msg.caption
                        self.reply_to_message = None
                
                mock_message = MockMessage(message, target_msg)
                
                # Process the file
                await auto_rename_files(client, mock_message)
                successful += 1
                
                # Small delay to prevent flooding
                await asyncio.sleep(1)
            else:
                failed += 1
                failed_list.append(f"{link} - No file found")
                
        except Exception as e:
            failed += 1
            failed_list.append(f"{link} - {str(e)[:50]}")
        
        # Update progress every 5 links
        if i % 5 == 0:
            await processing_msg.edit_text(
                f"🔗 **Processing {len(links)} links...**\n\n"
                f"{i}/{len(links)} completed\n"
                f"✅ Successful: {successful}\n"
                f"❌ Failed: {failed}"
            )
    
    # Final result
    result_text = f"✅ **Batch Processing Complete!**\n\n"
    result_text += f"**Total Links:** {len(links)}\n"
    result_text += f"**✅ Successful:** {successful}\n"
    result_text += f"**❌ Failed:** {failed}\n"
    
    if failed > 0:
        result_text += f"\n**Failed Links:**\n"
        for fail in failed_list[:10]:  # Show only first 10 failures
            result_text += f"• {fail}\n"
        if len(failed_list) > 10:
            result_text += f"... and {len(failed_list)-10} more"
    
    await processing_msg.edit_text(result_text)

@Client.on_message(filters.private & filters.command("link"))
async def link_command_handler(client: Client, message: Message):
    """Handle /link command"""
    user_id = message.from_user.id
    
    # Check if user is banned
    if await check_ban_status(user_id):
        return
    
    # Check verification
    if not await is_user_verified(user_id):
        await send_verification(client, message)
        return
    
    # Check command format
    if len(message.command) == 1:
        help_text = (
            "🔗 **Link Processor Help**\n\n"
            "**Usage:**\n"
            "`/link <telegram-file-link>` - Process a single file link\n"
            "`/link` (reply to message with links) - Process multiple links\n\n"
            "**Supported Formats:**\n"
            "• `https://t.me/c/1234567890/123` (private channel)\n"
            "• `https://t.me/username/123` (public channel/group)\n\n"
            "**Note:** For private channels, the bot must be a member and have appropriate permissions."
        )
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Tutorial", url="https://t.me/Animelibraryn4")],
            [InlineKeyboardButton("❌ Close", callback_data="close_data")]
        ])
        
        await message.reply_text(help_text, reply_markup=buttons)
        return
    
    # Process single link from command
    link = message.command[1]
    link_info = await extract_link_info(link)
    
    if not link_info:
        await message.reply_text(
            "❌ **Invalid link format!**\n\n"
            "Please provide a valid Telegram message link.\n"
            "Examples:\n"
            "• `https://t.me/c/1234567890/123`\n"
            "• `https://t.me/username/123`"
        )
        return
    
    await process_single_link(client, message, link_info)

@Client.on_message(filters.private & filters.regex(r'https?://t\.me/(c/|[a-zA-Z0-9_]+/\d+)') & ~filters.command(['start', 'help', 'link', 'ls']))
async def auto_link_handler(client: Client, message: Message):
    """Automatically handle Telegram links sent by users"""
    user_id = message.from_user.id
    
    # Check if user is banned
    if await check_ban_status(user_id):
        return
    
    # Check verification
    if not await is_user_verified(user_id):
        await send_verification(client, message)
        return
    
    # Extract all links from the message
    link_pattern = r'https?://t\.me/(?:c/\d+/\d+|(?:[a-zA-Z0-9_]+)/\d+)'
    links = re.findall(link_pattern, message.text)
    
    if not links:
        return
    
    # Prepend 't.me/' to make them full URLs
    full_links = [f"https://t.me/{link}" if not link.startswith('http') else link for link in links]
    
    if len(full_links) == 1:
        # Single link - process directly
        link_info = await extract_link_info(full_links[0])
        if link_info:
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Process Link", callback_data=f"process_link_{user_id}")],
                [InlineKeyboardButton("❌ Cancel", callback_data="close_data")]
            ])
            
            await message.reply_text(
                f"🔗 **Telegram Link Detected**\n\n"
                f"Do you want to process this link with auto-rename?\n\n"
                f"**Link:** `{full_links[0]}`",
                reply_markup=buttons
            )
            
            # Store link info for callback
            user_link_state[user_id] = {
                'link': full_links[0],
                'link_info': link_info,
                'message_id': message.id
            }
    else:
        # Multiple links - show options
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"✅ Process All ({len(full_links)} links)", callback_data=f"process_links_{user_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="close_data")]
        ])
        
        await message.reply_text(
            f"🔗 **{len(full_links)} Telegram Links Detected**\n\n"
            f"Do you want to process all links with auto-rename?",
            reply_markup=buttons
        )
        
        # Store links for callback
        user_link_state[user_id] = {
            'links': full_links,
            'message_id': message.id
        }

@Client.on_callback_query(filters.regex(r'^process_link_(\d+)$'))
async def process_link_callback(client, query: CallbackQuery):
    """Handle link processing callback"""
    user_id = int(query.matches[0].group(1))
    
    if user_id != query.from_user.id:
        await query.answer("This button is not for you!", show_alert=True)
        return
    
    if user_id not in user_link_state:
        await query.answer("Link information expired. Please send the link again.", show_alert=True)
        return
    
    link_data = user_link_state[user_id]
    
    await query.message.edit_text("⏳ **Processing link...**")
    
    try:
        await process_single_link(client, query.message, link_data['link_info'])
    except Exception as e:
        await query.message.edit_text(f"❌ **Error:** `{str(e)[:200]}`")
    finally:
        # Clean up
        if user_id in user_link_state:
            del user_link_state[user_id]

@Client.on_callback_query(filters.regex(r'^process_links_(\d+)$'))
async def process_links_callback(client, query: CallbackQuery):
    """Handle multiple links processing callback"""
    user_id = int(query.matches[0].group(1))
    
    if user_id != query.from_user.id:
        await query.answer("This button is not for you!", show_alert=True)
        return
    
    if user_id not in user_link_state or 'links' not in user_link_state[user_id]:
        await query.answer("Link information expired. Please send the links again.", show_alert=True)
        return
    
    link_data = user_link_state[user_id]
    
    await query.message.edit_text(f"⏳ **Processing {len(link_data['links'])} links...**")
    
    try:
        await process_multiple_links(client, query.message, link_data['links'])
    except Exception as e:
        await query.message.edit_text(f"❌ **Error:** `{str(e)[:200]}`")
    finally:
        # Clean up
        if user_id in user_link_state:
            del user_link_state[user_id]

# Add to help text
LINK_HELP_TEXT = """
🔗 **Link Processing Commands**

**/link <telegram-file-link>**
Process a single Telegram file link with auto-rename.

**/link** (reply to message)
Process multiple links from a replied message.

**Auto-detection:**
Simply send any Telegram file link and the bot will detect it automatically.

**Supported Link Formats:**
• `https://t.me/c/1234567890/123` - Private channels
• `https://t.me/username/123` - Public channels/groups

**Requirements for Private Channels:**
1. Bot must be added to the channel
2. Bot needs appropriate permissions to access files
"""
#[file content end]

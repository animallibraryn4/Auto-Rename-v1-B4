import os
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymediainfo import MediaInfo # You need to install this: pip install pymediainfo
from helper.database import codeflixbots

# Set to track users in /info mode to temporarily disable auto-rename
info_mode_users = set()

@Client.on_message(filters.private & filters.command("info"))
async def info_command(client, message):
    user_id = message.from_user.id
    info_mode_users.add(user_id) 
    
    cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_info")]])
    
    ask_msg = await message.reply_text(
        "**Please send the file you want to analyze.**\n\n"
        "• Auto-rename is paused.\n"
        "• Sending another command will cancel this.",
        reply_markup=cancel_btn
    )

    try:
        response = await client.listen(chat_id=user_id, filters=filters.private, timeout=300)
        
        if response.text and response.text.startswith("/"):
            info_mode_users.discard(user_id)
            return

        if not (response.document or response.video or response.audio):
            await response.reply_text("❌ This is not a valid file. /info mode stopped.")
            info_mode_users.discard(user_id)
            return

        ms = await response.reply_text("`🔍 Downloading metadata and analyzing...`")
        
        # 1. Download the file header/media to analyze
        # MediaInfo usually needs the physical file
        path = await response.download()
        media_info = MediaInfo.parse(path)
        
        file_data = response.document or response.video or response.audio
        file_name = getattr(file_data, "file_name", "Unknown_File")
        user_name = message.from_user.first_name
        date_str = datetime.now().strftime("%B %d, %Y")

        # 2. Parse General Info
        general = media_info.general_tracks[0]
        v_count = len(media_info.video_tracks)
        a_count = len(media_info.audio_tracks)
        s_count = len(media_info.text_tracks)

        # 3. Format the Output String
        text = f"📊 **Media Information**\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"📁 **File:** `{file_name}`\n"
        text += f"🗓️ **Date:** {date_str}\n"
        text += f"👤 **Requested by:** {user_name}\n"
        text += f"📦 **Size:** {round(general.file_size / (1024*1024), 2)} MB\n\n"
        
        text += f"📌 **General Information**\n"
        text += f"• **Format:** {general.format}\n"
        # Convert ms to HH:MM:SS
        duration_ms = general.duration or 0
        text += f"• **Duration:** {time.strftime('%H:%M:%S', time.gmtime(duration_ms/1000))}\n"
        text += f"• **Bitrate:** {int(general.overall_bit_rate/1000) if general.overall_bit_rate else 'N/A'} kb/s\n\n"

        # 4. Video Streams
        text += f"🎬 **Video Streams:** {v_count}\n"
        for i, v in enumerate(media_info.video_tracks, 1):
            text += f"\n**Video #{i}**\n"
            text += f"  Codec: {v.codec_id.lower() if v.codec_id else v.format.lower()}\n"
            text += f"  Resolution: {v.width}x{v.height}\n"
            text += f"  FPS: {v.frame_rate}\n"

        # 5. Audio Streams
        text += f"\n🎵 **Audio Streams:** {a_count}\n"
        for i, a in enumerate(media_info.audio_tracks, 1):
            text += f"\n**Audio #{i}**\n"
            text += f"  Codec: {a.format.lower()}\n"
            text += f"  Channels: {a.channel_s}\n"
            text += f"  Sample Rate: {a.sampling_rate} Hz\n"
            text += f"  Language: {a.language if a.language else 'und'}\n"

        # 6. Subtitle Streams
        if s_count > 0:
            text += f"\n💬 **Subtitle Streams:** {s_count}\n"
            for i, s in enumerate(media_info.text_tracks, 1):
                text += f"\n**Subtitle #{i}**\n"
                text += f"  Format: {s.format.lower()}\n"
                text += f"  Language: {s.language if s.language else 'und'}\n"

        await ms.edit_text(text)
        
        # Cleanup: Remove downloaded file to save disk space
        if os.path.exists(path):
            os.remove(path)

    except asyncio.TimeoutError:
        await ask_msg.edit_text("❌ Time limit exceeded. /info mode closed.")
    except Exception as e:
        print(f"Info Error: {e}")
        await ms.edit_text(f"❌ Error analyzing file: {e}")
    finally:
        info_mode_users.discard(user_id)
        

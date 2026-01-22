import re, os, time
from os import environ, getenv
id_pattern = re.compile(r'^.\d+$') 

class Config(object):

    @staticmethod
    def get_force_sub_channels():
        channels = []
        for i in range(1, 6):
            channel_id = getattr(Config, f'FORCE_SUB_CHANNELS{i}', None)
            if channel_id and channel_id != 'None':
                try:
                    channels.append(int(channel_id))
                except ValueError:
                    channels.append(channel_id)
        return channels
        
    # pyro client config
    API_ID    = os.environ.get("API_ID", "")
    API_HASH  = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
    # database config
    DB_NAME = os.environ.get("DB_NAME","nikhil7858978052")     
    DB_URL  = os.environ.get("DB_URL","mongodb+srv://mikota4432:jkJDQuZH6o8pxxZe@cluster0.2vngilq.mongodb.net/?retryWrites=true&w=majority")
    PORT = os.environ.get("PORT", "9090")
    # other configs
    BOT_UPTIME  = time.time()
    START_PIC   = os.environ.get("START_PIC", "https://images8.alphacoders.com/138/1384114.png")
    ADMIN       = [int(admin) if id_pattern.search(admin) else admin for admin in os.environ.get('ADMIN', '5380609667').split()]        
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002263636517"))
    DUMP_CHANNEL = int(os.environ.get("DUMP_CHANNEL", "-1001896877147"))
    WEBHOOK = bool(os.environ.get("WEBHOOK", "True")) 
    # Force Subscribe Channels (up to 5) - Use Channel IDs
    FORCE_SUB_CHANNELS1 = None  # Channel ID 1 (required) 
    FORCE_SUB_CHANNELS2 = None  # Set to channel ID string or None
    FORCE_SUB_CHANNELS3 = None  # Set to channel ID string or None
    FORCE_SUB_CHANNELS4 = None  # Set to channel ID string or None
    FORCE_SUB_CHANNELS5 = None  # Set to channel ID string or None
  
    SEASON_PLACEHOLDER = "{season}"  

    
class Txt(object):

    START_TXT = """👋 ʜᴇʏ, {}!  

ɪ ᴀᴍ ᴀ ᴘᴏᴡᴇʀꜰᴜʟ **ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ʙᴏᴛ** ᴡɪᴛʜ ᴀᴅᴠᴀɴᴄᴇᴅ ꜰᴇᴀᴛᴜʀᴇꜱ!

🚀 **ᴋᴇʏ ꜰᴇᴀᴛᴜʀᴇꜱ:**
✅ **ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ:** ꜰɪʟᴇ & ᴄᴀᴘᴛɪᴏɴ ᴍᴏᴅᴇꜱ
✅ **ꜱᴇǫᴜᴇɴᴄᴇ ᴍᴏᴅᴇ:** ʙᴀᴛᴄʜ ʀᴇɴᴀᴍᴇ ᴇᴘɪꜱᴏᴅᴇꜱ ɪɴ ᴏʀᴅᴇʀ
✅ **ꜱᴍᴀʀᴛ ᴛʜᴜᴍʙɴᴀɪʟ:** ꜱᴇᴛ ᴅɪꜰꜰᴇʀᴇɴᴛ ᴛʜᴜᴍʙꜱ ꜰᴏʀ 480ᴘ, 720ᴘ, 1080ᴘ
✅ **ᴍᴇᴛᴀᴅᴀᴛᴀ:** ᴄᴜꜱᴛᴏᴍ ᴛɪᴛʟᴇ, ᴀᴜᴛʜᴏʀ & ᴀʀᴛɪꜱᴛ ᴇᴅɪᴛɪɴɢ
✅ **ꜰɪʟᴇ ᴄᴏɴᴠᴇʀᴛ:** ᴠɪᴅᴇᴏ ᴛᴏ ꜰɪʟᴇ & ᴠɪᴄᴇ-ᴠᴇʀꜱᴀ

💳 **ᴘʀᴇᴍɪᴜᴍ:** ᴄʜᴇᴄᴋ ᴏᴜʀ ᴀꜰꜰᴏʀᴅᴀʙʟᴇ ᴘʟᴀɴꜱ ᴜꜱɪɴɢ /plan

💡 ᴜꜱᴇ /tutorial ᴛᴏ ʟᴇᴀʀɴ ʜᴏᴡ ᴛᴏ ꜱᴇᴛ ꜰᴏʀᴍᴀᴛꜱ!

🤖 **ᴘᴏᴡᴇʀᴇᴅ ʙʏ:** @animelibraryn4"""
      
    FILE_NAME_TXT = """<b><pre>⚙️ ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ꜱᴇᴛᴜᴘ</pre></b>

ᴀᴜᴛᴏ-ʀᴇɴᴀᴍᴇ ꜱʏꜱᴛᴇᴍ ꜰɪʟᴇ ɴᴀᴍᴇ ꜱᴇ ꜱᴇᴀꜱᴏɴ, ᴇᴘɪꜱᴏᴅᴇ ᴀᴜʀ ǫᴜᴀʟɪᴛʏ ᴋᴏ ᴀᴜᴛᴏ-ᴅᴇᴛᴇᴄᴛ ᴋᴀʀᴛᴀ ʜᴀɪ.

✨ **ᴀᴠᴀɪʟᴀʙʟᴇ ᴠᴀʀɪᴀʙʟᴇꜱ:**
➲ `[EP.NUM]` : ᴇᴘɪꜱᴏᴅᴇ ɴᴜᴍʙᴇʀ (ᴇɢ: 01, 02)
➲ `[SE.NUM]` : ꜱᴇᴀꜱᴏɴ ɴᴜᴍʙᴇʀ (ᴇɢ: 01, 02)
➲ `[QUALITY]` : ᴠɪᴅᴇᴏ ʀᴇꜱᴏʟᴜᴛɪᴏɴ (ᴇɢ: 720ᴘ, 1080ᴘ)

📝 **ʜᴏᴡ ᴛᴏ ꜱᴇᴛ:**
ᴜꜱᴇ `/autorename` ꜰᴏʟʟᴏᴡᴇᴅ ʙʏ ʏᴏᴜʀ ᴅᴇꜱɪʀᴇᴅ ꜰᴏʀᴍᴀᴛ.

💡 **ᴇxᴀᴍᴘʟᴇ:**
`/autorename Naruto S[SE.NUM] - E[EP.NUM] [QUALITY] @Animelibraryn4`

✅ **ᴘʀᴏ ᴛɪᴘ:**
ᴀɢᴀʀ ᴏʀɪɢɪɴᴀʟ ꜰɪʟᴇ ɴᴀᴍᴇ ᴍᴇɪɴ `S01E05` ʏᴀ `Episode 05` ʟɪᴋʜᴀ ʜᴀɪ, ᴛᴏ ʙᴏᴛ ᴜꜱᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴘɪᴄᴋ ᴋᴀʀ ʟᴇɢᴀ. ᴀɢᴀʀ ᴀᴀᴘ ᴄᴀᴘᴛɪᴏɴ ꜱᴇ ᴅᴇᴛᴀɪʟꜱ ɴɪᴋᴀʟɴᴀ ᴄʜᴀʜᴛᴇ ʜᴀɪɴ, ᴛᴏ `/mode` ꜱᴇ **Caption Mode** ꜱᴇʟᴇᴄᴛ ᴋᴀʀᴇɪɴ."""
    
    
    ABOUT_TXT = f"""<b>❍ ᴍʏ ɴᴀᴍᴇ : <a href="https://t.me/animelibraryn4">ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ</a>
❍ ᴅᴇᴠᴇʟᴏᴩᴇʀ : <a href="https://t.me/animelibraryn4">ᴀɴɪᴍᴇ ʟɪʙʀᴀʀʏ ɴ4</a>
❍ ɢɪᴛʜᴜʙ : <a href="https://t.me/animelibraryn4">ᴀɴɪᴍᴇ ʟɪʙʀᴀʀʏ ɴ4</a>
❍ ʟᴀɴɢᴜᴀɢᴇ : <a href="https://www.python.org/">ᴘʏᴛʜᴏɴ</a>
❍ ᴅᴀᴛᴀʙᴀꜱᴇ : <a href="https://www.mongodb.com/">ᴍᴏɴɢᴏ ᴅʙ</a>
❍ ʜᴏꜱᴛᴇᴅ ᴏɴ : <a href="https://t.me/animelibraryn4">ᴠᴘs</a>
❍ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ : <a href="https://t.me/animelibraryn4">ᴀɴɪᴍᴇ ʟɪʙʀᴀʀʏ ɴ4</a>"""

    THUMBNAIL_TXT = """<b><pre>🖼️ ᴛʜᴜᴍʙɴᴀɪʟ ᴍᴀɴᴀɢᴇʀ</pre></b>

➲ /smart_thumb : ᴏᴘᴇɴ ᴍᴇɴᴜ ᴛᴏ ᴍᴀɴᴀɢᴇ ᴛʜᴜᴍʙɴᴀɪʟꜱ ꜰᴏʀ ᴇᴀᴄʜ ǫᴜᴀʟɪᴛʏ (480ᴘ, 720ᴘ, 1080ᴘ, ᴇᴛᴄ).

🌟 **ꜰᴇᴀᴛᴜʀᴇꜱ:**
✅ **ꜱᴘᴇᴄɪꜰɪᴄ ᴛʜᴜᴍʙ:** ꜱᴇᴛ ᴅɪꜰꜰᴇʀᴇɴᴛ ᴛʜᴜᴍʙꜱ ꜰᴏʀ ᴅɪꜰꜰᴇʀᴇɴᴛ ᴠɪᴅᴇᴏ ǫᴜᴀʟɪᴛɪᴇꜱ.
✅ **ɢʟᴏʙᴀʟ ᴛʜᴜᴍʙ:** ꜱᴇᴛ ᴏɴᴇ ᴛʜᴜᴍʙɴᴀɪʟ ꜰᴏʀ ᴀʟʟ ʏᴏᴜʀ ꜰɪʟᴇꜱ ᴀᴛ ᴏɴᴄᴇ.
✅ **ᴀᴜᴛᴏ ᴅᴇᴛᴇᴄᴛ:** ʙᴏᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴘɪᴄᴋꜱ ᴛʜᴇ ʀɪɢʜᴛ ᴛʜᴜᴍʙ ʙᴀꜱᴇᴅ ᴏɴ ᴠɪᴅᴇᴏ ʀᴇꜱᴏʟᴜᴛɪᴏɴ.

📝 **ʜᴏᴡ ᴛᴏ ꜱᴇᴛ:**
1️⃣ ᴄʟɪᴄᴋ ᴏɴ ᴀ ǫᴜᴀʟɪᴛʏ ʙᴜᴛᴛᴏɴ (ᴇ.ɢ., 720ᴘ).
2️⃣ ꜱᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ ᴛᴏ ꜱᴀᴠᴇ ɪᴛ ꜰᴏʀ ᴛʜᴀᴛ ǫᴜᴀʟɪᴛʏ.
3️⃣ ᴜꜱᴇ 👀 **ᴠɪᴇᴡ** ᴏʀ 🗑️ **ᴅᴇʟᴇᴛᴇ** ʙᴜᴛᴛᴏɴꜱ ᴛᴏ ᴍᴀɴᴀɢᴇ.

📌 **ɴᴏᴛᴇ:** ɪꜰ ɴᴏ ᴄᴜꜱᴛᴏᴍ ᴛʜᴜᴍʙ ɪꜱ ꜱᴇᴛ, ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ᴜꜱᴇ ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ꜰɪʟᴇ'ꜱ ᴛʜᴜᴍʙɴᴀɪʟ."""
    
    
    CAPTION_TXT = """<b><pre>📝 ᴄᴀᴘᴛɪᴏɴ ᴍᴀɴᴀɢᴇʀ</pre></b>

➲ /set_caption : ꜱᴇᴛ ʏᴏᴜʀ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ.
➲ /see_caption : ᴠɪᴇᴡ ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴄᴀᴘᴛɪᴏɴ.
➲ /del_caption : ʀᴇꜱᴇᴛ ᴄᴀᴘᴛɪᴏɴ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ.

✨ **ᴀᴠᴀɪʟᴀʙʟᴇ ᴠᴀʀɪᴀʙʟᴇꜱ:**
📂 `{filename}` : ᴏʀɪɢɪɴᴀʟ ꜰɪʟᴇ ɴᴀᴍᴇ
⚖️ `{filesize}` : ꜰɪʟᴇ ꜱɪᴢᴇ (ᴍʙ/ɢʙ)
⏰ `{duration}` : ᴠɪᴅᴇᴏ ʟᴇɴɢᴛʜ
⚙️ `{metadata}` : ᴄᴜꜱᴛᴏᴍ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴛᴇxᴛ

📌 **ᴇxᴀᴍᴘʟᴇ:**
`/set_caption 🎬 ɴᴀᴍᴇ: {filename} \n⚖️ ꜱɪᴢᴇ: {filesize} \n💎 ᴘᴏᴡᴇʀᴇᴅ ʙʏ: @Animelibraryn4`

⚠️ **ᴍᴇᴅɪᴀ ᴛʏᴘᴇ:**
ʏᴏᴜ ᴄᴀɴ ᴄʜᴏᴏꜱᴇ ᴛᴏ ʀᴇᴄᴇɪᴠᴇ ꜰɪʟᴇꜱ ᴀꜱ **ᴅᴏᴄᴜᴍᴇɴᴛ** ᴏʀ **ꜱᴛʀᴇᴀᴍᴀʙʟᴇ ᴠɪᴅᴇᴏ** ᴠɪᴀ ᴛʜᴇ /settings ᴍᴇɴᴜ."""
    

    PROGRESS_BAR = """\n
<b>» Size</b> : {1} | {2}
<b>» Done</b> : {0}%
<b>» Speed</b> : {3}/s
<b>» ETA</b> : {4} """
    
    
    DONATE_TXT = """<b><pre>💖 sᴜᴘᴘᴏʀᴛ ᴏᴜʀ ᴘʀᴏᴊᴇᴄᴛ</pre></b>

<blockquote>ᴛʜᴀɴᴋꜱ ꜰᴏʀ ꜱʜᴏᴡɪɴɢ ɪɴᴛᴇʀᴇꜱᴛ ɪɴ ꜱᴜᴘᴘᴏʀᴛɪɴɢ ᴜꜱ!</blockquote>

ɪꜰ ʏᴏᴜ ꜰɪɴᴅ ᴏᴜʀ ʙᴏᴛ ᴜꜱᴇꜰᴜʟ, ᴄᴏɴꜱɪᴅᴇʀ ᴅᴏɴᴀᴛɪɴɢ. ʏᴏᴜʀ ᴄᴏɴᴛʀɪʙᴜᴛɪᴏɴ ʜᴇʟᴘꜱ ᴜꜱ ᴋᴇᴇᴘ ᴛʜᴇ ꜱᴇʀᴠᴇʀꜱ ʀᴜɴɴɪɴɢ ᴀɴᴅ ᴛʜᴇ ʙᴏᴛ ᴀᴅ-ꜰʀᴇᴇ.

💰 **ᴅᴏɴᴀᴛᴇ ᴠɪᴀ ᴜᴘɪ:**
➲ ᴜᴘɪ ɪᴅ: <code>nikhil7858978052-1@okaxis</code> 
*(ᴛᴀᴘ ᴛᴏ ᴄᴏᴘʏ)*

⭐ **ᴡʜʏ ᴅᴏɴᴀᴛᴇ?**
✅ ꜰᴀꜱᴛᴇʀ ꜰɪʟᴇ ᴘʀᴏᴄᴇꜱꜱɪɴɢ
✅ ɴᴇᴡ ꜰᴇᴀᴛᴜʀᴇ ᴅᴇᴠᴇʟᴏᴘᴍᴇɴᴛ
✅ ꜱᴇʀᴠᴇʀ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ

🎁 **ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ:**
ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ʙᴇɴᴇꜰɪᴛꜱ ʟɪᴋᴇ **ɴᴏ ᴛᴏᴋᴇɴꜱ** ᴀɴᴅ **ʜɪɢʜ ᴘʀɪᴏʀɪᴛʏ**, ᴄʜᴇᴄᴋ ᴏᴜʀ ᴘʟᴀɴꜱ ᴜꜱɪɴɢ /plan.

📸 **ꜱᴇɴᴅ ꜱᴄʀᴇᴇɴꜱʜᴏᴛ:** ᴀꜰᴛᴇʀ ᴘᴀʏᴍᴇɴᴛ, ꜱᴇɴᴅ ᴛʜᴇ ʀᴇᴄᴇɪᴘᴛ ᴛᴏ @Animelibraryn4"""

    
    PREMIUM_TXT = """<b>ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ sᴇʀᴠɪᴄᴇ ᴀɴᴅ ᴇɴJᴏʏ ᴇxᴄʟᴜsɪᴠᴇ ғᴇᴀᴛᴜʀᴇs:
○ ᴜɴʟɪᴍɪᴛᴇᴅ Rᴇɴᴀᴍɪɴɢ: ʀᴇɴᴀᴍᴇ ᴀs ᴍᴀɴʏ ғɪʟᴇs ᴀs ʏᴏᴜ ᴡᴀɴᴛ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ ʀᴇsᴛʀɪᴄᴛɪᴏɴs.
○ ᴇᴀʀʟʏ Aᴄᴄᴇss: ʙᴇ ᴛʜᴇ ғɪʀsᴛ ᴛᴏ ᴛᴇsᴛ ᴀɴᴅ ᴜsᴇ ᴏᴜʀ ʟᴀᴛᴇsᴛ ғᴇᴀᴛᴜʀᴇs ʙᴇғᴏʀᴇ ᴀɴʏᴏɴᴇ ᴇʟsᴇ.

• ᴜꜱᴇ /plan ᴛᴏ ꜱᴇᴇ ᴀʟʟ ᴏᴜʀ ᴘʟᴀɴꜱ ᴀᴛ ᴏɴᴄᴇ.

➲ ғɪʀsᴛ sᴛᴇᴘ : ᴘᴀʏ ᴛʜᴇ ᴀᴍᴏᴜɴᴛ ᴀᴄᴄᴏʀᴅɪɴɢ ᴛᴏ ʏᴏᴜʀ ғᴀᴠᴏʀɪᴛᴇ ᴘʟᴀɴ ᴛᴏ ᴛʜɪs rohit162@fam ᴜᴘɪ ɪᴅ.

➲ secoɴᴅ sᴛᴇᴘ : ᴛᴀᴋᴇ ᴀ sᴄʀᴇᴇɴsʜᴏᴛ ᴏғ ʏᴏᴜʀ ᴘᴀʏᴍᴇɴᴛ ᴀɴᴅ sʜᴀʀᴇ ɪᴛ ᴅɪʀᴇᴄᴛʟʏ ʜᴇʀᴇ: @sewxiy 

➲ ᴀʟᴛᴇʀɴᴀᴛɪᴠᴇ sᴛᴇᴘ : ᴏʀ ᴜᴘʟᴏᴀᴅ ᴛʜᴇ sᴄʀᴇᴇɴsʜᴏᴛ ʜᴇʀᴇ ᴀɴᴅ ʀᴇᴘʟʏ ᴡɪᴛʜ ᴛʜᴇ /bought ᴄᴏᴍᴍᴀɴᴅ.

Yᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ ᴡɪʟʟ ʙᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴀғᴛᴇʀ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ</b>"""

    PREPLANS_TXT = """<b><pre>🎖️ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀɴs:</pre>

Pʀɪᴄɪɴɢ:
➜ ᴍᴏɴᴛʜʟʏ ᴘʀᴇᴍɪᴜᴍ: ₹109/ᴍᴏɴᴛʜ
➜ ᴅᴀɪʟʏ ᴘʀᴇᴍɪᴜᴍ: ₹19/ᴅᴀʏ
➜ ᴄᴏɴᴛᴀᴄᴛ: @Anime_Library_N4

➲ ᴜᴘɪ ɪᴅ - <code>@</code>

‼️ᴜᴘʟᴏᴀᴅ ᴛʜᴇ ᴘᴀʏᴍᴇɴᴛ sᴄʀᴇᴇɴsʜᴏᴛ ʜᴇʀᴇ ᴀɴᴅ ʀᴇᴘʟʏ ᴡɪᴛʜ ᴛʜᴇ /bought ᴄᴏᴍᴍᴀɴᴅ.</b>"""
    
    HELP_TXT = """<b><pre>🛠️ ʙᴏᴛ ʜᴇʟᴘ ᴍᴇɴᴜ</pre></b>

ʀᴇɴᴀᴍᴇ ʙᴏᴛ ɪꜱ ᴀ ᴘᴏᴡᴇʀꜰᴜʟ ᴛᴏᴏʟ ᴛᴏ ᴍᴀɴᴀɢᴇ, ʀᴇɴᴀᴍᴇ, ᴀɴᴅ ᴏᴘᴛɪᴍɪᴢᴇ ʏᴏᴜʀ ᴍᴇᴅɪᴀ ᴇꜰꜰᴏʀᴛʟᴇꜱꜱʟʏ.

🚀 **ᴄᴏʀᴇ ꜰᴇᴀᴛᴜʀᴇꜱ:**
➲ /autorename : ꜱᴇᴛ ᴀᴜᴛᴏ-ʀᴇɴᴀᴍᴇ ꜰᴏʀᴍᴀᴛ (ᴇɢ: [EP.NUM]).
➲ /mode : ꜱᴡɪᴛᴄʜ ʙᴇᴛᴡᴇᴇɴ **ꜰɪʟᴇ** ᴏʀ **ᴄᴀᴘᴛɪᴏɴ** ᴍᴏᴅᴇ.
➲ /smart_thumb : ᴍᴀɴᴀɢᴇ ǫᴜᴀʟɪᴛʏ-ᴡɪꜱᴇ ᴛʜᴜᴍʙɴᴀɪʟꜱ.
➲ /metadata : ᴇᴅɪᴛ ᴠɪᴅᴇᴏ ᴛɪᴛʟᴇ, ᴀᴜᴛʜᴏʀ & ᴀʀᴛɪꜱᴛ.

📂 **ʙᴀᴛᴄʜ & sᴇǫᴜᴇɴᴄᴇ:**
➲ /sequence : ꜱᴛᴀʀᴛ ʙᴀᴛᴄʜ ʀᴇɴᴀᴍɪɴɢ ꜰᴏʀ ᴇᴘɪꜱᴏᴅᴇꜱ.
➲ /ls : ʀᴇɴᴀᴍᴇ ꜰɪʟᴇꜱ ᴅɪʀᴇᴄᴛʟʏ ꜰʀᴏᴍ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋꜱ.
➲ /fileseq : ᴄʜᴏᴏꜱᴇ ꜰʟᴏᴡ (ᴇᴘɪꜱᴏᴅᴇ ↔️ ǫᴜᴀʟɪᴛʏ).

💎 **ꜱᴇʀᴠɪᴄᴇꜱ:**
➲ /plan : ᴠɪᴇᴡ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ & ᴘʀɪᴄɪɴɢ.
➲ /get_token : ᴠᴇʀɪꜰʏ ʏᴏᴜʀꜱᴇʟꜰ ᴛᴏ ᴜꜱᴇ ꜰʀᴇᴇ ʟɪᴍɪᴛꜱ.
➲ /tutorial : ʟᴇᴀʀɴ ʜᴏᴡ ᴛᴏ ᴜꜱᴇ ᴀᴜᴛᴏ-ʀᴇɴᴀᴍᴇ.

⚠️ **ɴᴏᴛᴇ:** ᴍᴀᴋᴇ ꜱᴜʀᴇ ʏᴏᴜ ᴀʀᴇ ᴠᴇʀɪꜰɪᴇᴅ ᴠɪᴀ /get_token ᴛᴏ ᴇɴᴊᴏʏ ᴜɴɪɴᴛᴇʀʀᴜᴘᴛᴇᴅ ꜱᴇʀᴠɪᴄᴇ."""

    SEND_METADATA = """
<b><pre>🛠️ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴍᴀɴᴀɢᴇʀ</pre></b>

➲ /metadata : ᴛᴏɢɢʟᴇ ᴍᴇᴛᴀᴅᴀᴛᴀ ᴏɴ/ᴏꜰꜰ.

📝 **ᴡʜᴀᴛ ɪᴛ ᴅᴏᴇꜱ?**
ᴡʜᴇɴ ᴇɴᴀʙʟᴇᴅ, ɪᴛ ᴄᴜꜱᴛᴏᴍɪᴢᴇꜱ ᴛʜᴇ ɪɴᴛᴇʀɴᴀʟ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ᴏꜰ ʏᴏᴜʀ **ᴍᴋᴠ/ᴍᴘ4** ꜰɪʟᴇꜱ, ɪɴᴄʟᴜᴅɪɴɢ ᴀᴜᴅɪᴏ ᴛʀᴀᴄᴋꜱ, ꜱᴜʙᴛɪᴛʟᴇꜱ, ᴀɴᴅ ᴠɪᴅᴇᴏ ꜱᴛʀᴇᴀᴍꜱ.

✨ **ʏᴏᴜ ᴄᴀɴ ꜱᴇᴛ ᴄᴜꜱᴛᴏᴍ:**
🏷️ **ᴛɪᴛʟᴇ:** `Encoded By N4_Bots`
👤 **ᴀᴜᴛʜᴏʀ:** `@N4_Bots`
🎨 **ᴀʀᴛɪꜱᴛ:** `Animelibraryn4`

💡 **ʜᴏᴡ ᴛᴏ ᴇᴅɪᴛ?**
ᴀꜰᴛᴇʀ ᴛʏᴘɪɴɢ /metadata, ᴜꜱᴇ ᴛʜᴇ ɪɴʟɪɴᴇ ʙᴜᴛᴛᴏɴꜱ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴇᴀᴄʜ ꜰɪᴇʟᴅ ᴘᴇʀꜱᴏɴᴀʟʟʏ.
"""

    SOURCE_TXT = """
<b>👋 ʜᴇʏ!
ᴛʜɪs ɪs ᴀɴ ᴀᴅᴠᴀɴᴄᴇᴅ **ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ʙᴏᴛ**,
ᴀ ᴘʀɪᴠᴀᴛᴇ ᴀɴᴅ ʜɪɢʜ-ᴘᴇʀꜰᴏʀᴍᴀɴᴄᴇ ᴛᴇʟᴇɢʀᴀᴍ ᴇɴɢɪɴᴇ.</b>

✨ **ᴘʀᴏᴊᴇᴄᴛ ʜɪɢʜʟɪɢʜᴛꜱ:**
🚀 **ᴀᴜᴛᴏ-ᴘᴀʀsɪɴɢ:** ꜱᴍᴀʀᴛʟʏ ᴇxᴛʀᴀᴄᴛꜱ ꜱᴇᴀꜱᴏɴ/ᴇᴘɪꜱᴏᴅᴇ ꜰʀᴏᴍ ɴᴀᴍᴇꜱ ᴏʀ ᴄᴀᴘᴛɪᴏɴꜱ.
💎 **ꜱᴇǫᴜᴇɴᴄᴇ ᴍᴏᴅᴇ:** ᴘʀᴏᴄᴇꜱꜱ ᴇɴᴛɪʀᴇ ᴀɴɪᴍᴇ/ꜱᴇʀɪᴇꜱ ʙᴀᴛᴄʜᴇꜱ ᴇꜰꜰᴏʀᴛʟᴇꜱꜱʟʏ.
🖼️ **ᴍᴜʟᴛɪ-ᴛʜᴜᴍʙ:** ᴅɪꜰꜰᴇʀᴇɴᴛ ᴛʜᴜᴍʙɴᴀɪʟꜱ ꜰᴏʀ ᴇᴀᴄʜ ᴠɪᴅᴇᴏ ʀᴇꜱᴏʟᴜᴛɪᴏɴ.
🔒 **ᴘʀɪᴠᴀᴄʏ:** ꜱᴇᴄᴜʀᴇ ᴜꜱᴇʀ ᴅᴀᴛᴀ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ ᴡɪᴛʜ ᴍᴏɴɢᴏᴅʙ.

📢 **ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ:** @Animelibraryn4
"""

    META_TXT = """
**ᴍᴇᴛᴀᴅᴀᴛᴀ ʜᴇʟᴘ**

ᴍᴇᴛᴀᴅᴀᴛᴀ ᴄᴏɴᴛʀᴏʟꜱ ʜᴏᴡ ʏᴏᴜʀ ꜰɪʟᴇꜱ ᴀʀᴇ ɴᴀᴍᴇᴅ ᴀɴᴅ ꜱʜᴏᴡɴ ɪɴ ᴘʟᴀʏᴇʀꜱ ᴀɴᴅ ᴛᴇʟᴇɢʀᴀᴍ.

**ʏᴏᴜ ᴄᴀɴ ᴄʜᴀɴɢᴇ:**

• **ᴛɪᴛʟᴇ** – ᴛʜᴇ ᴍᴀɪɴ ɴᴀᴍᴇ ᴏꜰ ᴛʜᴇ ᴍᴇᴅɪᴀ
• **ᴀᴜᴛʜᴏʀ** – ᴛʜᴇ ᴄʀᴇᴀᴛᴏʀ ᴏʀ ᴜᴘʟᴏᴀᴅᴇʀ  
• **ᴀʀᴛɪꜱᴛ** – ᴛʜᴇ ᴀʀᴛɪꜱᴛ ᴏʀ ꜱᴛᴜᴅɪᴏ  
• **ᴀᴜᴅɪᴏ** – ᴀᴜᴅɪᴏ ᴛʀᴀᴄᴋ ᴛɪᴛʟᴇ  
• **ꜱᴜʙᴛɪᴛʟᴇ** – ꜱᴜʙᴛɪᴛʟᴇ ᴛʀᴀᴄᴋ ɴᴀᴍᴇ  
• **ᴠɪᴅᴇᴏ** – ᴠɪᴅᴇᴏ ᴛɪᴛʟᴇ ᴏʀ ꜰᴏʀᴍᴀᴛ

**ᴇxᴀᴍᴘʟᴇ:** ᴛᴀᴘ ᴀɴʏ ʙᴜᴛᴛᴏɴ ᴛᴏ ꜱᴇᴛ ᴀ ᴠᴀʟᴜᴇ, ᴛʜᴇɴ ꜱᴇɴᴅ ᴛʜᴇ ᴛᴇxᴛ.

**ᴛʜᴇꜱᴇ ᴏᴘᴛɪᴏɴꜱ ʟᴇᴛ ʏᴏᴜ ᴄᴏɴᴛʀᴏʟ ᴇxᴀᴄᴛʟʏ ʜᴏᴡ ʏᴏᴜʀ ᴍᴇᴅɪᴀ ɪꜱ ᴘʀᴇꜱᴇɴᴛᴇᴅ.**
"""

    PLAN_MAIN_TXT = "<b>👋 Hey, {}!\n\nSelect a plan that suits your needs from the options below:</b>"
    
    FREE_TXT = "🆓 Free Trial\n⏰ 1 hour access\n💸 Plan price ➛ Free\n\n➛ Limited-time access to test the service\n➛ Perfect to check speed and features\n➛ No payment required"
    
    BASIC_TXT = "🟢 Basic Pass\n⏰ 7 days\n💸 Plan price ➛ ₹39\n\n➛ Suitable for light and short-term users\n➛ Full access during active period\n➛ Budget-friendly weekly plan\n➛ Check your active plan: /myplan"
    
    LITE_TXT = "🔵 Lite Plan\n⏰ 15 days\n💸 Plan price ➛ ₹79\n\n➛ Best choice for regular users\n➛ More value compared to weekly plan\n➛ Smooth and uninterrupted access\n➛ Recommended for consistent usage"
    
    STANDARD_TXT = "⭐ Standard Plan\n⏰ 30 days\n💸 Plan price ➛ ₹129\n\n➛ Most popular plan\n➛ Best balance of price and duration\n➛ Ideal for daily and long-term users\n➛ ⭐ Best for regular users"
    
    PRO_TXT = "💎 Pro Plan\n⏰ 50 days\n💸 Plan price ➛ ₹199\n\n➛ Maximum savings for long-term users\n➛ Hassle-free extended access\n➛ Best value plan for power users\n➛ 💎 Long-term recommended"
    
    ULTRA_TXT = "👑 Ultra Plan\n⏰ Coming soon\n💸 Price ➛ TBA\n\n➛ Premium and exclusive access\n➛ Extra benefits and features\n➛ Designed for hardcore users\n➛ Stay tuned for launch 👀"

    SELECT_PAYMENT_TXT = "<b>Select Your Payment Method</b>"
    
    UPI_TXT = "👋 Hey {},\n\nPay the amount according to your selected plan and enjoy plan membership!\n\n💵 <b>UPI ID:</b> <code>dm @PYato</code>\n\n‼️ You must send a screenshot after payment."
    
    QR_TXT = "👋 Hey {},\n\nPay the amount according to your membership price!\n\n📸 <b>QR Code:</b> <a href='https://t.me/Animelibraryn4'>Click here to scan</a>\n\n‼️ You must send a screenshot after payment."


    

# Multi-language strings for the dating bot

LANGUAGES = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 हिन्दी",
    "es": "🇪🇸 Español",
    "ar": "🇸🇦 العربية",
    "ru": "🇷🇺 Русский",
}

STRINGS = {
    "en": {
        "choose_language": "🌍 <b>Please choose your language:</b>",
        "language_set": "✅ Language set to English.",
        "welcome": "👋 <b>Welcome to the Dating Bot!</b>\n\nFind people nearby, match, and connect on Telegram.",
        "need_sub": "⚠️ <b>Please subscribe to our channels first:</b>",
        "sub_done": "✅ Subscribed! Continue.",
        "ask_age": "🎂 <b>Step 1/6 — How old are you?</b>\n\nSend your age as a number (e.g. 24).",
        "invalid_age": "❌ Please send a valid age between 18 and 99.",
        "ask_name": "📝 <b>Step 2/6 — What is your name?</b>",
        "invalid_name": "❌ Name must be 2–40 characters.",
        "ask_gender": "⚧ <b>Step 3/6 — What is your gender?</b>",
        "male": "👨 Male",
        "female": "👩 Female",
        "ask_pref": "💘 <b>Step 4/6 — Who do you want to see?</b>",
        "both": "👫 Both",
        "ask_bio": "✍️ <b>Step 5/6 — Write a short bio about yourself.</b>\n\n(Send any text, or /skip to skip.)",
        "ask_city": "🏙 <b>Step 6/6 — Your City?</b>",
        "ask_country": "🌎 <b>Now send your Country.</b>",
        "profile_done": "🎉 <b>Your profile is complete!</b>\n\nLet's start discovering people near you...",
        "profile_preview": "👤 <b>Your Profile</b>",
        "name": "Name",
        "age": "Age",
        "gender": "Gender",
        "looking_for": "Looking for",
        "city": "City",
        "country": "Country",
        "bio": "Bio",
        "no_more_profiles": "😔 No more profiles nearby.\nCome back later!",
        "like": "❤️ Like",
        "unlike": "👎 Unlike",
        "message": "💬 Message",
        "report": "🚩 Report",
        "liked": "❤️ You liked this profile!",
        "unliked": "👎 Skipped.",
        "reported": "🚩 Report sent to admin. Thanks!",
        "new_like_notif": "🔔 <b>Someone liked your profile!</b>\n\nTap below to view their profile.",
        "view_liker": "👀 View Profile",
        "interested": "💚 Interested",
        "not_interested": "💔 Not Interested",
        "match": "🎊 <b>It's a Match!</b>\n\nYou both are interested. Here are the Telegram profiles:\n\n{user1}\n{user2}",
        "not_interested_thanks": "💔 Okay, we'll move on.",
        "profile_liked_already": "You already liked this profile.",
        "please_register": "📝 Please register first with /start",
        "daily_limit": "⏳ You've reached your daily like limit. Try again tomorrow.",
        "safety_tip": "🚨 Safety Tip: Never share financial info.",
        "profile_menu": "⚙️ <b>Profile Menu</b>",
        "edit_profile": "✏️ Edit Profile",
        "my_profile": "👤 My Profile",
        "delete_profile": "🗑 Delete Profile",
        "settings": "⚙️ Settings",
        "profile_deleted": "🗑 Your profile has been deleted.",
        "help": (
            "<b>🤖 Dating Bot Help</b>\n\n"
            "/start — Register / show main menu\n"
            "/profile — View your profile\n"
            "/discover — Find nearby people\n"
            "/matches — View your matches\n"
            "/help — Show this help"
        ),
    },
    "hi": {
        "choose_language": "🌍 <b>कृपया अपनी भाषा चुनें:</b>",
        "language_set": "✅ भाषा हिंदी में सेट हो गई।",
        "welcome": "👋 <b>डेटिंग बॉट में आपका स्वागत है!</b>\n\nआस-पास के लोगों से मिलें, मैच करें और Telegram पर जुड़ें।",
        "need_sub": "⚠️ <b>कृपया पहले हमारे चैनल सब्सक्राइब करें:</b>",
        "sub_done": "✅ सब्सक्राइब हो गया! जारी रखें।",
        "ask_age": "🎂 <b>चरण 1/6 — आपकी उम्र क्या है?</b>\n\nअपनी उम्र एक संख्या में भेजें (जैसे 24)।",
        "invalid_age": "❌ कृपया 18 से 99 के बीच वैध उम्र भेजें।",
        "ask_name": "📝 <b>चरण 2/6 — आपका नाम क्या है?</b>",
        "invalid_name": "❌ नाम 2–40 अक्षरों का होना चाहिए।",
        "ask_gender": "⚧ <b>चरण 3/6 — आपका लिंग क्या है?</b>",
        "male": "👨 पुरुष",
        "female": "👩 महिला",
        "ask_pref": "💘 <b>चरण 4/6 — आप किसे देखना चाहते हैं?</b>",
        "both": "👫 दोनों",
        "ask_bio": "✍️ <b>चरण 5/6 — अपने बारे में थोड़ा लिखें।</b>\n\n(कोई भी टेक्स्ट भेजें, या /skip से छोड़ें।)",
        "ask_city": "🏙 <b>चरण 6/6 — आपका शहर?</b>",
        "ask_country": "🌎 <b>अब अपना देश भेजें।</b>",
        "profile_done": "🎉 <b>आपकी प्रोफ़ाइल तैयार है!</b>\n\nआइए आस-पास के लोगों को ढूंढें...",
        "profile_preview": "👤 <b>आपकी प्रोफ़ाइल</b>",
        "name": "नाम",
        "age": "उम्र",
        "gender": "लिंग",
        "looking_for": "देख रहे हैं",
        "city": "शहर",
        "country": "देश",
        "bio": "बायो",
        "no_more_profiles": "😔 आस-पास कोई और प्रोफ़ाइल नहीं मिली।\nबाद में फिर आएं!",
        "like": "❤️ लाइक",
        "unlike": "👎 स्किप",
        "message": "💬 संदेश",
        "report": "🚩 रिपोर्ट",
        "liked": "❤️ आपने लाइक कर दिया!",
        "unliked": "👎 स्किप कर दिया।",
        "reported": "🚩 रिपोर्ट भेज दी गई। धन्यवाद!",
        "new_like_notif": "🔔 <b>किसी ने आपकी प्रोफ़ाइल लाइक की!</b>\n\nउनकी प्रोफ़ाइल देखने के लिए नीचे टैप करें।",
        "view_liker": "👀 प्रोफ़ाइल देखें",
        "interested": "💚 इंट्रेस्टेड",
        "not_interested": "💔 नॉट इंट्रेस्टेड",
        "match": "🎊 <b>यह मैच है!</b>\n\nआप दोनों इंट्रेस्टेड हैं। Telegram प्रोफ़ाइल यहाँ हैं:\n\n{user1}\n{user2}",
        "not_interested_thanks": "💔 ठीक है, हम आगे बढ़ते हैं।",
        "profile_liked_already": "आप पहले ही इस प्रोफ़ाइल को लाइक कर चुके हैं।",
        "please_register": "📝 कृपया पहले /start से रजिस्टर करें",
        "daily_limit": "⏳ आपकी आज की लाइक सीमा पूरी हो गई। कल फिर कोशिश करें।",
        "safety_tip": "🚨 सुरक्षा सुझाव: कभी भी वित्तीय जानकारी साझा न करें।",
        "profile_menu": "⚙️ <b>प्रोफ़ाइल मेनू</b>",
        "edit_profile": "✏️ प्रोफ़ाइल संपादित करें",
        "my_profile": "👤 मेरी प्रोफ़ाइल",
        "delete_profile": "🗑 प्रोफ़ाइल हटाएं",
        "settings": "⚙️ सेटिंग्स",
        "profile_deleted": "🗑 आपकी प्रोफ़ाइल हटा दी गई है।",
        "help": (
            "<b>🤖 डेटिंग बॉट सहायता</b>\n\n"
            "/start — रजिस्टर / मुख्य मेनू\n"
            "/profile — अपनी प्रोफ़ाइल देखें\n"
            "/discover — आस-पास के लोग खोजें\n"
            "/matches — अपने मैच देखें\n"
            "/help — सहायता"
        ),
    },
    # Add more languages the same way...
}

# Fill missing languages with English as fallback
for code in LANGUAGES:
    if code not in STRINGS:
        STRINGS[code] = STRINGS["en"]


def t(lang: str, key: str, **kwargs) -> str:
    """Translate helper."""
    lang = lang if lang in STRINGS else "en"
    text = STRINGS[lang].get(key) or STRINGS["en"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from languages import LANGUAGES, t


def language_kb():
    rows, row = [], []
    for code, label in LANGUAGES.items():
        row.append(InlineKeyboardButton(label, callback_data=f"lang:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def sub_kb(lang):
    from config import FSUB_CHANNEL, FSUB_CHANNEL_2, FSUB_CHANNEL_3
    rows = []
    for ch in [FSUB_CHANNEL, FSUB_CHANNEL_2, FSUB_CHANNEL_3]:
        if ch and ch != 0:
            rows.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/c/{str(ch)[4:]}" if str(ch).startswith("-100") else f"https://t.me/{ch}")])
    rows.append([InlineKeyboardButton("✅ I've Joined", callback_data="sub:done")])
    return InlineKeyboardMarkup(rows)


def gender_kb(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "male"), callback_data="gender:male")],
        [InlineKeyboardButton(t(lang, "female"), callback_data="gender:female")],
    ])


def pref_kb(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "male"), callback_data="pref:male")],
        [InlineKeyboardButton(t(lang, "female"), callback_data="pref:female")],
        [InlineKeyboardButton(t(lang, "both"), callback_data="pref:both")],
    ])


def profile_actions_kb(lang, target_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "like"), callback_data=f"act:like:{target_id}")],
        [InlineKeyboardButton(t(lang, "unlike"), callback_data=f"act:unlike:{target_id}")],
        [InlineKeyboardButton(t(lang, "message"), callback_data=f"act:msg:{target_id}")],
        [InlineKeyboardButton(t(lang, "report"), callback_data=f"act:report:{target_id}")],
    ])


def interested_kb(lang, liker_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "interested"), callback_data=f"resp:yes:{liker_id}")],
        [InlineKeyboardButton(t(lang, "not_interested"), callback_data=f"resp:no:{liker_id}")],
    ])


def main_menu_kb(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Discover", callback_data="menu:discover")],
        [InlineKeyboardButton(t(lang, "my_profile"), callback_data="menu:profile")],
        [InlineKeyboardButton("💚 Matches", callback_data="menu:matches")],
        [InlineKeyboardButton(t(lang, "edit_profile"), callback_data="menu:edit")],
        [InlineKeyboardButton(t(lang, "settings"), callback_data="menu:settings")],
    ])

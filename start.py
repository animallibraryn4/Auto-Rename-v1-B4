from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import FSUB_CHANNEL, FSUB_CHANNEL_2, FSUB_CHANNEL_3
from languages import t
from keyboards import language_kb, sub_kb
from database import get_user, create_or_update_user


async def is_subscribed(client, user_id):
    channels = [c for c in [FSUB_CHANNEL, FSUB_CHANNEL_2, FSUB_CHANNEL_3] if c and c != 0]
    if not channels:
        return True
    for ch in channels:
        try:
            m = await client.get_chat_member(ch, user_id)
            if m.status in ("left", "kicked"):
                return False
        except UserNotParticipant:
            return False
        except Exception:
            # If bot can't check, don't block the user
            continue
    return True


def setup_start_handlers(app):

    @app.on_message(filters.command("start") & filters.private)
    async def start_cmd(client, message):
        user_id = message.from_user.id
        user = get_user(user_id)

        # Existing registered user
        if user and user.get("profile_complete"):
            lang = user.get("language", "en")
            await message.reply_text(
                t(lang, "welcome"),
                reply_markup=main_menu_kb_inline(lang),
            )
            return

        # New user → ask language first
        if not user or "language" not in user:
            await message.reply_text(
                t("en", "choose_language"),
                reply_markup=language_kb(),
            )
            return

        # User chose language but not subscribed
        lang = user.get("language", "en")
        if not await is_subscribed(client, user_id):
            await message.reply_text(t(lang, "need_sub"), reply_markup=sub_kb(lang))
            return

        # Start profile creation
        create_or_update_user(user_id, profile_step="age")
        await message.reply_text(t(lang, "ask_age"))

    @app.on_callback_query(filters.regex(r"^lang:"))
    async def pick_lang(client, cb):
        lang = cb.data.split(":")[1]
        user_id = cb.from_user.id
        create_or_update_user(user_id, language=lang, profile_step="sub")
        await cb.message.edit_text(t(lang, "language_set"))

        if not await is_subscribed(client, user_id):
            await cb.message.reply_text(t(lang, "need_sub"), reply_markup=sub_kb(lang))
        else:
            create_or_update_user(user_id, profile_step="age")
            await cb.message.reply_text(t(lang, "ask_age"))

    @app.on_callback_query(filters.regex(r"^sub:done$"))
    async def sub_done(client, cb):
        user_id = cb.from_user.id
        user = get_user(user_id) or {}
        lang = user.get("language", "en")

        if not await is_subscribed(client, user_id):
            await cb.answer(t(lang, "need_sub"), show_alert=True)
            return
        create_or_update_user(user_id, profile_step="age")
        await cb.message.edit_text(t(lang, "sub_done"))
        await cb.message.reply_text(t(lang, "ask_age"))


def main_menu_kb_inline(lang):
    from keyboards import main_menu_kb
    return main_menu_kb(lang)


# Re-export for imports
from keyboards import main_menu_kb

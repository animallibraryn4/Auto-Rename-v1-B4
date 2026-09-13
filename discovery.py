from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from languages import t
from keyboards import profile_actions_kb
from database import (
    get_user, get_candidates, mark_seen, has_liked, add_like,
)
from profile import render_profile


async def send_next_profile(client, user_id: int, chat_id: int, reply_to: int = None):
    """Find next matching profile and send to user."""
    user = get_user(user_id)
    if not user or not user.get("profile_complete"):
        await client.send_message(chat_id, "📝 Please register first with /start")
        return

    lang = user.get("language", "en")
    pref = user.get("gender_pref", "both")
    city = user.get("city", "")
    country = user.get("country", "")

    candidates = get_candidates(user_id, pref, city=city, country=country, limit=5)
    # Pick first candidate not yet seen
    target = None
    for c in candidates:
        mark_seen(user_id, c["user_id"])
        target = c
        break

    if not target:
        await client.send_message(chat_id, t(lang, "no_more_profiles"))
        return

    caption = render_profile(lang, target, title="💘 Profile")
    caption += f"\n\n<i>{t(lang,'safety_tip')}</i>"

    try:
        if target.get("photo_file_id"):
            await client.send_photo(
                chat_id,
                photo=target["photo_file_id"],
                caption=caption,
                reply_markup=profile_actions_kb(lang, target["user_id"]),
            )
        else:
            await client.send_message(
                chat_id,
                caption,
                reply_markup=profile_actions_kb(lang, target["user_id"]),
            )
    except Exception as e:
        print("send_next_profile error:", e)


def setup_discovery_handlers(app):

    @app.on_message(filters.command("discover") & filters.private)
    async def cmd_discover(client, message):
        await send_next_profile(client, message.from_user.id, message.chat.id)

    @app.on_callback_query(filters.regex(r"^act:(like|unlike|msg|report):(\d+)$"))
    async def act_cb(client, cb):
        action, target_id = cb.data.split(":")[1], int(cb.data.split(":")[2])
        user_id = cb.from_user.id
        user = get_user(user_id) or {}
        lang = user.get("language", "en")

        if action == "like":
            if has_liked(user_id, target_id):
                await cb.answer(t(lang, "profile_liked_already"), show_alert=True)
            else:
                add_like(user_id, target_id)
                await cb.answer(t(lang, "liked"))
                # Notify target
                await notify_like(client, target_id, user_id)
            # Next profile
            await cb.message.delete()
            await send_next_profile(client, user_id, cb.message.chat.id)

        elif action == "unlike":
            await cb.answer(t(lang, "unliked"))
            await cb.message.delete()
            await send_next_profile(client, user_id, cb.message.chat.id)

        elif action == "msg":
            target = get_user(target_id) or {}
            username = target.get("username")
            if username:
                await cb.answer(url=f"https://t.me/{username}")
            else:
                await cb.answer("❌ User has no public username.", show_alert=True)

        elif action == "report":
            from database import add_report
            add_report(user_id, target_id)
            await cb.answer(t(lang, "reported"), show_alert=True)
            await cb.message.delete()
            await send_next_profile(client, user_id, cb.message.chat.id)


async def notify_like(client, target_id: int, liker_id: int):
    """Notify target that someone liked them."""
    target = get_user(target_id)
    if not target:
        return
    lang = target.get("language", "en")
    try:
        from keyboards import interested_kb
        await client.send_message(
            target_id,
            t(lang, "new_like_notif"),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(lang, "view_liker"),
                                      callback_data=f"resp:view:{liker_id}")],
            ]),
        )
    except Exception as e:
        print("notify_like error:", e)

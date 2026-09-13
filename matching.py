from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from languages import t
from keyboards import interested_kb
from database import (
    get_user, create_match, get_matches, is_mutual, has_liked,
)
from profile import render_profile


def setup_matching_handlers(app):

    # ---------- VIEW LIKER ----------
    @app.on_callback_query(filters.regex(r"^resp:view:(\d+)$"))
    async def view_liker(client, cb):
        liker_id = int(cb.data.split(":")[2])
        user_id = cb.from_user.id
        user = get_user(user_id) or {}
        lang = user.get("language", "en")

        liker = get_user(liker_id)
        if not liker:
            await cb.answer("User no longer available.", show_alert=True)
            return

        caption = render_profile(lang, liker, title="👀 Liked You")
        try:
            await cb.message.edit_text(
                caption,
                reply_markup=interested_kb(lang, liker_id),
            )
        except Exception:
            await cb.message.reply_text(
                caption,
                reply_markup=interested_kb(lang, liker_id),
            )

    # ---------- INTERESTED / NOT INTERESTED ----------
    @app.on_callback_query(filters.regex(r"^resp:(yes|no):(\d+)$"))
    async def resp_cb(client, cb):
        answer, other_id = cb.data.split(":")[1], int(cb.data.split(":")[2])
        user_id = cb.from_user.id
        user = get_user(user_id) or {}
        lang = user.get("language", "en")

        if answer == "no":
            await cb.answer(t(lang, "not_interested_thanks"))
            try:
                await cb.message.delete()
            except Exception:
                pass
            return

        # Interested → check mutual
        if not has_liked(user_id, other_id):
            # Record user's like too
            from database import add_like
            add_like(user_id, other_id)

        if is_mutual(user_id, other_id):
            create_match(user_id, other_id)
            await send_match_notifications(client, user_id, other_id)
            try:
                await cb.message.delete()
            except Exception:
                pass
        else:
            await cb.answer("💚 Interest sent!", show_alert=True)
            try:
                await cb.message.edit_text("💚 Interest sent!")
            except Exception:
                pass


async def send_match_notifications(client, a: int, b: int):
    ua = get_user(a) or {}
    ub = get_user(b) or {}

    def fmt(u):
        un = u.get("username")
        name = u.get("name", "User")
        if un:
            return f"• <a href='https://t.me/{un}'>{name}</a>"
        return f"• <a href='tg://user?id={u['user_id']}'>{name}</a>"

    for uid, lang_key in [(a, ua.get("language", "en")), (b, ub.get("language", "en"))]:
        try:
            await client.send_message(
                uid,
                t(lang_key, "match",
                  user1=fmt(ua), user2=fmt(ub)),
                disable_web_page_preview=True,
            )
        except Exception as e:
            print("send_match_notifications error:", e)


async def show_matches(client, user_id: int, chat_id: int):
    user = get_user(user_id) or {}
    lang = user.get("language", "en")
    ms = get_matches(user_id)
    if not ms:
        await client.send_message(chat_id, "💔 No matches yet.")
        return

    text = "<b>💚 Your Matches</b>\n\n"
    for m in ms:
        other_id = m["user2"] if m["user1"] == user_id else m["user1"]
        other = get_user(other_id) or {}
        un = other.get("username")
        name = other.get("name", "User")
        if un:
            text += f"• <a href='https://t.me/{un}'>{name}</a>\n"
        else:
            text += f"• <a href='tg://user?id={other_id}'>{name}</a>\n"

    await client.send_message(chat_id, text, disable_web_page_preview=True,
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton("🔍 Discover More",
                                                        callback_data="menu:discover")],
                              ]))


def setup_match_command(app):
    @app.on_message(filters.command("matches") & filters.private)
    async def cmd_matches(client, message):
        await show_matches(client, message.from_user.id, message.chat.id)

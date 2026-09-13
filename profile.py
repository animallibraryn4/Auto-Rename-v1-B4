from pyrogram import filters
from languages import t
from keyboards import gender_kb, pref_kb, main_menu_kb
from database import get_user, create_or_update_user, update_field
from start import is_subscribed


def setup_profile_handlers(app):

    # ---------- MESSAGE HANDLER FOR PROFILE STEPS ----------
    @app.on_message(filters.private & ~filters.command(["start", "help", "profile",
                                                         "discover", "matches"]))
    async def profile_step_handler(client, message):
        user_id = message.from_user.id
        user = get_user(user_id)
        if not user:
            return
        step = user.get("profile_step")
        lang = user.get("language", "en")

        if step == "age":
            text = (message.text or "").strip()
            if not text.isdigit() or not (18 <= int(text) <= 99):
                await message.reply_text(t(lang, "invalid_age"))
                return
            update_field(user_id, "age", int(text))
            update_field(user_id, "profile_step", "name")
            await message.reply_text(t(lang, "ask_name"))

        elif step == "name":
            text = (message.text or "").strip()
            if not (2 <= len(text) <= 40):
                await message.reply_text(t(lang, "invalid_name"))
                return
            update_field(user_id, "name", text)
            update_field(user_id, "profile_step", "gender")
            await message.reply_text(t(lang, "ask_gender"), reply_markup=gender_kb(lang))

        elif step == "bio":
            bio = (message.text or "").strip()
            if message.text and message.text.startswith("/skip"):
                bio = ""
            update_field(user_id, "bio", bio[:300])
            update_field(user_id, "profile_step", "city")
            await message.reply_text(t(lang, "ask_city"))

        elif step == "city":
            text = (message.text or "").strip()
            if not text:
                return
            update_field(user_id, "city", text[:60])
            update_field(user_id, "profile_step", "country")
            await message.reply_text(t(lang, "ask_country"))

        elif step == "country":
            text = (message.text or "").strip()
            if not text:
                return
            update_field(user_id, "country", text[:60])
            update_field(user_id, "profile_step", "done")
            update_field(user_id, "profile_complete", True)
            await message.reply_text(t(lang, "profile_done"))
            await message.reply_text(
                t(lang, "profile_menu"),
                reply_markup=main_menu_kb(lang),
            )
            # Trigger first discovery
            from discovery import send_next_profile
            await send_next_profile(client, user_id, message.chat.id)

    # ---------- CALLBACK HANDLERS ----------
    @app.on_callback_query(filters.regex(r"^gender:"))
    async def pick_gender(client, cb):
        val = cb.data.split(":")[1]
        user_id = cb.from_user.id
        user = get_user(user_id) or {}
        lang = user.get("language", "en")
        update_field(user_id, "gender", val)
        update_field(user_id, "profile_step", "pref")
        await cb.message.edit_text(t(lang, "ask_pref"), reply_markup=pref_kb(lang))

    @app.on_callback_query(filters.regex(r"^pref:"))
    async def pick_pref(client, cb):
        val = cb.data.split(":")[1]
        user_id = cb.from_user.id
        user = get_user(user_id) or {}
        lang = user.get("language", "en")
        update_field(user_id, "gender_pref", val)
        update_field(user_id, "profile_step", "bio")
        await cb.message.edit_text(t(lang, "ask_bio"))

    # ---------- /profile COMMAND ----------
    @app.on_message(filters.command("profile") & filters.private)
    async def cmd_profile(client, message):
        if not await is_subscribed(client, message.from_user.id):
            return
        user_id = message.from_user.id
        user = get_user(user_id)
        if not user or not user.get("profile_complete"):
            await message.reply_text("📝 Please register first with /start")
            return
        lang = user.get("language", "en")
        await message.reply_text(
            render_profile(lang, user, title=t(lang, "profile_preview")),
            reply_markup=main_menu_kb(lang),
        )

    # ---------- Profile menu callbacks ----------
    @app.on_callback_query(filters.regex(r"^menu:"))
    async def menu_cb(client, cb):
        action = cb.data.split(":")[1]
        user_id = cb.from_user.id
        user = get_user(user_id) or {}
        lang = user.get("language", "en")

        if action == "profile":
            await cb.message.edit_text(
                render_profile(lang, user, title=t(lang, "profile_preview")),
                reply_markup=main_menu_kb(lang),
            )
        elif action == "discover":
            from discovery import send_next_profile
            await send_next_profile(client, user_id, cb.message.chat.id)
        elif action == "matches":
            from matching import show_matches
            await show_matches(client, user_id, cb.message.chat.id)
        elif action == "edit":
            update_field(user_id, "profile_step", "age")
            await cb.message.edit_text(t(lang, "ask_age"))
        elif action == "settings":
            update_field(user_id, "profile_step", "age")
            await cb.message.edit_text("⚙️ Edit your profile. " + t(lang, "ask_age"))


def render_profile(lang, u, title="👤 Profile"):
    gender = u.get("gender", "?").capitalize()
    pref = u.get("gender_pref", "?").capitalize()
    lines = [
        f"<b>{title}</b>\n",
        f"<b>{t(lang,'name')}:</b> {u.get('name','-')}",
        f"<b>{t(lang,'age')}:</b> {u.get('age','-')}",
        f"<b>{t(lang,'gender')}:</b> {gender}",
        f"<b>{t(lang,'looking_for')}:</b> {pref}",
        f"<b>{t(lang,'city')}:</b> {u.get('city','-')}",
        f"<b>{t(lang,'country')}:</b> {u.get('country','-')}",
        f"<b>{t(lang,'bio')}:</b> {u.get('bio') or '-'}",
    ]
    return "\n".join(lines)

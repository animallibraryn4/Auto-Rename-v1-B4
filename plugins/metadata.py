from helper.database import n4bots as db
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import Txt


# ────────────────── UI HELPERS ────────────────── #

def meta_buttons_home(status):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🟢 Metadata ON" if status == "On" else "⚪ Metadata ON",
                callback_data="meta_on"
            ),
            InlineKeyboardButton(
                "🔴 Metadata OFF" if status == "Off" else "⚪ Metadata OFF",
                callback_data="meta_off"
            )
        ],
        [
            InlineKeyboardButton("✏️ Title", callback_data="edit_title"),
            InlineKeyboardButton("👤 Author", callback_data="edit_author")
        ],
        [
            InlineKeyboardButton("🎨 Artist", callback_data="edit_artist"),
            InlineKeyboardButton("🎵 Audio", callback_data="edit_audio")
        ],
        [
            InlineKeyboardButton("💬 Subtitle", callback_data="edit_subtitle"),
            InlineKeyboardButton("🎬 Video", callback_data="edit_video")
        ],
        [
            InlineKeyboardButton("♻️ Reset All", callback_data="meta_reset"),
            InlineKeyboardButton("📖 Help", callback_data="meta_help")
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="meta_close")
        ]
    ])


def meta_buttons_edit(field):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Set New Value", callback_data=f"set_{field}"),
            InlineKeyboardButton("🗑 Clear", callback_data=f"clear_{field}")
        ],
        [
            InlineKeyboardButton("⬅️ Back", callback_data="meta_home"),
            InlineKeyboardButton("❌ Close", callback_data="meta_close")
        ]
    ])


# ────────────────── SUMMARY ────────────────── #

async def meta_summary(user_id):
    return f"""
🎛 **Metadata Panel**

**Status:** `{await db.get_metadata(user_id)}`

**Title:** `{await db.get_title(user_id) or 'Not set'}`
**Author:** `{await db.get_author(user_id) or 'Not set'}`
**Artist:** `{await db.get_artist(user_id) or 'Not set'}`
**Audio:** `{await db.get_audio(user_id) or 'Not set'}`
**Subtitle:** `{await db.get_subtitle(user_id) or 'Not set'}`
**Video:** `{await db.get_video(user_id) or 'Not set'}`
"""


# ────────────────── /metadata ────────────────── #

@Client.on_message(filters.command("metadata"))
async def metadata_cmd(client, message):
    uid = message.from_user.id
    text = await meta_summary(uid)
    await message.reply_text(
        text,
        reply_markup=meta_buttons_home(await db.get_metadata(uid)),
        disable_web_page_preview=True
    )


# ────────────────── CALLBACK HANDLER ────────────────── #

@Client.on_callback_query()
async def metadata_cb(client, q: CallbackQuery):
    uid = q.from_user.id
    data = q.data

    if data == "meta_on":
        await db.set_metadata(uid, "On")
        await q.answer("Metadata Enabled")

    elif data == "meta_off":
        await db.set_metadata(uid, "Off")
        await q.answer("Metadata Disabled")

    elif data.startswith("edit_"):
        field = data.split("_")[1]
        value = await getattr(db, f"get_{field}")(uid)
        await q.message.edit_text(
            f"✏️ **Edit {field.capitalize()}**\n\nCurrent:\n`{value or 'Not set'}`",
            reply_markup=meta_buttons_edit(field)
        )
        return

    elif data.startswith("set_"):
        field = data.split("_")[1]
        await db.col.update_one(
            {"_id": uid},
            {"$set": {"edit_field": field}},
            upsert=True
        )
        await q.message.edit_text(
            f"📝 Send new **{field.capitalize()}** value now.\n\nUse /cancel to stop."
        )
        return

    elif data.startswith("clear_"):
        field = data.split("_")[1]
        await getattr(db, f"set_{field}")(uid, "")
        await q.answer(f"{field.capitalize()} cleared")

    elif data == "meta_reset":
        await db.set_title(uid, "")
        await db.set_author(uid, "")
        await db.set_artist(uid, "")
        await db.set_audio(uid, "")
        await db.set_subtitle(uid, "")
        await db.set_video(uid, "")
        await q.answer("All metadata reset")

    elif data == "meta_help":
        await q.message.edit_text(
            Txt.META_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back", callback_data="meta_home")]
            ])
        )
        return

    elif data == "meta_home":
        await q.message.edit_text(
            await meta_summary(uid),
            reply_markup=meta_buttons_home(await db.get_metadata(uid))
        )
        return

    elif data == "meta_close":
        await q.message.delete()
        return

    await q.message.edit_text(
        await meta_summary(uid),
        reply_markup=meta_buttons_home(await db.get_metadata(uid))
    )


# ────────────────── INPUT HANDLER ────────────────── #

@Client.on_message(filters.private & filters.text & ~filters.command)
async def meta_input(client, message):
    uid = message.from_user.id
    user = await db.col.find_one({"_id": uid})

    if not user or "edit_field" not in user:
        return

    field = user["edit_field"]
    await getattr(db, f"set_{field}")(uid, message.text.strip())

    await db.col.update_one(
        {"_id": uid},
        {"$unset": {"edit_field": ""}}
    )

    await message.reply_text(
        f"✅ **{field.capitalize()} Updated**",
        reply_markup=meta_buttons_home(await db.get_metadata(uid))
    )


@Client.on_message(filters.command("cancel"))
async def meta_cancel(client, message):
    await db.col.update_one(
        {"_id": message.from_user.id},
        {"$unset": {"edit_field": ""}}
    )
    await message.reply_text("❌ Metadata edit cancelled.")

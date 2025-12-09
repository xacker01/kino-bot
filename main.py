# bot.py
import logging
import sqlite3
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================== SOZLAMALAR ======================
BOT_TOKEN = "8533869240:AAHkyCghf6V1fVVw-gB-R66RqvvrxuokUYM"

ADMIN_IDS = {7872470445}  # <-- Admin user id (integer)

REQUIRED_CHANNELS = [
    ("@kinochi_kuuu", "1-Kanal")
]

DB_PATH = "media_codes.db"

# =====================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== SQLITE ===========================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS codes (
            code TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_name TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def save_code(code: str, file_id: str, file_type: str, file_name: Optional[str]):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "REPLACE INTO codes (code, file_id, file_type, file_name) VALUES (?, ?, ?, ?)",
        (code, file_id, file_type, file_name)
    )
    conn.commit()
    conn.close()


def get_by_code(code: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT file_id, file_type, file_name FROM codes WHERE code = ?", (code,))
    row = cur.fetchone()
    conn.close()
    return row


def remove_code(code: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM codes WHERE code = ?", (code,))
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0


def list_codes():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT code, file_type, file_name FROM codes ORDER BY code")
    rows = cur.fetchall()
    conn.close()
    return rows

# ================== YORDAMCHI =========================
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def is_user_subscribed(bot, user_id):
    for channel_username, _ in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

# ================== HANDLERLAR =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot

    subscribed = await is_user_subscribed(bot, user_id)

    if not subscribed:
        buttons = [[InlineKeyboardButton(ch_name, url=f"https://t.me/{ch_username[1:]}")]
                   for ch_username, ch_name in REQUIRED_CHANNELS]
        buttons.append([InlineKeyboardButton(" ✅ Obuna bo‘ldim!", callback_data="check_sub")])
        keyboard = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            "❗ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=keyboard
        )
        return

    await update.message.reply_text("Assalomu alaykum! Iltimos kodni yozing:")


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    bot = context.bot

    subscribed = await is_user_subscribed(bot, user_id)
    if subscribed:
        await query.edit_message_text("Assalomu alaykum! Iltimos kodni yozing:")
    else:
        buttons = [[InlineKeyboardButton(ch_name, url=f"https://t.me/{ch_username[1:]}")]
                   for ch_username, ch_name in REQUIRED_CHANNELS]
        buttons.append([InlineKeyboardButton(" ✅ Obuna bo‘ldim!", callback_data="check_sub")])
        keyboard = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "❗ Siz hali barcha kanallarga obuna bo‘lmagansiz!\nIltimos, quyidagi kanallarga obuna bo‘ling:",
            reply_markup=keyboard
        )


async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("Siz admin emassiz.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Foydalanish: reply qilib /add <kod>")
        return

    code = context.args[0].strip()
    if not update.message.reply_to_message:
        await update.message.reply_text("Iltimos, /add <kod> ni media ustiga REPLY qilib yuboring.")
        return

    src = update.message.reply_to_message
    file_id = file_type = file_name = None

    if src.photo:
        file_id = src.photo[-1].file_id
        file_type = "photo"
    elif src.video:
        file_id = src.video.file_id
        file_type = "video"
        file_name = src.video.file_name
    elif src.document:
        file_id = src.document.file_id
        file_type = "document"
        file_name = src.document.file_name
    else:
        await update.message.reply_text("Rasm, video yoki hujjat bo‘lishi kerak.")
        return

    save_code(code, file_id, file_type, file_name)
    await update.message.reply_text(f"✅ Kod `{code}` uchun media saqlandi.", parse_mode="Markdown")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Foydalanish: /remove <kod>")
        return

    code = context.args[0].strip()
    ok = remove_code(code)
    if ok:
        await update.message.reply_text(f"❌ Kod `{code}` o‘chirildi.", parse_mode="Markdown")
    else:
        await update.message.reply_text("Bunday kod yo‘q.")


async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz.")
        return

    rows = list_codes()
    if not rows:
        await update.message.reply_text("Hozircha kodlar yo‘q.")
        return

    result = "\n".join(f"{code} — {ftype}" for code, ftype, _ in rows)
    await update.message.reply_text(result)


async def clear_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Siz admin emassiz.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM codes")
    conn.commit()
    conn.close()
    await update.message.reply_text("🗑 Baza tozalandi! Barcha kodlar o‘chirildi.")


async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bot = context.bot

    subscribed = await is_user_subscribed(bot, user_id)
    if not subscribed:
        buttons = [[InlineKeyboardButton(ch_name, url=f"https://t.me/{ch_username[1:]}")]
                   for ch_username, ch_name in REQUIRED_CHANNELS]
        buttons.append([InlineKeyboardButton("Obuna bo‘ldim!", callback_data="check_sub")])
        keyboard = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            "❗ Botdan foydalanish uchun avval kanallarga obuna bo‘ling:",
            reply_markup=keyboard
        )
        return

    code = update.message.text.strip()
    row = get_by_code(code)
    if not row:
        await update.message.reply_text("Bu kod bo‘yicha hech narsa topilmadi!")
        return

    file_id, file_type, file_name = row
    if file_type == "photo":
        await update.message.reply_photo(photo=file_id)
    elif file_type == "video":
        await update.message.reply_video(video=file_id)
    elif file_type == "document":
        await update.message.reply_document(document=file_id, filename=file_name)
    else:
        await update.message.reply_text("Noma’lum media turi.")

# ================== MAIN ==============================
def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlerlarni qo‘shish
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))
    app.add_handler(CommandHandler("add", add_code))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("listcodes", list_cmd))
    app.add_handler(CommandHandler("cleardb", clear_db))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()

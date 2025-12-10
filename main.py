import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 7872470445

MEDIA_DB = {}

REQUIRED_CHANNELS = [
    ("@kinochi_kuuu", "https://t.me/kinochi_kuuu"),
]


async def check_subscription(user_id, context: ContextTypes.DEFAULT_TYPE):
    for channel, _ in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_subscription(user_id, context):
        keyboard = [
            [InlineKeyboardButton(name, url=url)] 
            for name, url in REQUIRED_CHANNELS
        ]
        keyboard.append([InlineKeyboardButton(" ✅Obuna bo‘ldim", callback_data="check_sub")])

        await update.message.reply_text(
            "❗Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text("Assalomu alaykum! Kodni kiriting:")


async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    if await check_subscription(user_id, context):
        await query.message.edit_text("Rahmat! Endi kodni kiriting:")
    else:
        await query.message.edit_text(" ❌Hali ham obuna bo‘lmadingiz! Obuna bo‘lib qayta urinib ko‘ring.")


async def add_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Siz admin emassiz!")
        return

    await update.message.reply_text(" ✏️Kodni yuboring:")
    context.user_data["waiting_code"] = True


async def save_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_code"):
        code = update.message.text
        context.user_data["code"] = code
        context.user_data["waiting_code"] = False
        context.user_data["waiting_media"] = True

        await update.message.reply_text("Endi faylni yuboring:")
        return


async def save_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_media"):
        code = context.user_data["code"]

        file_id = (
            update.message.video.file_id if update.message.video else
            update.message.document.file_id if update.message.document else
            update.message.photo[-1].file_id
        )

        MEDIA_DB[code] = file_id
        context.user_data["waiting_media"] = False

        await update.message.reply_text("✅Saqlangan!")
        return


async def send_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text

    if code in MEDIA_DB:
        await update.message.reply_video(MEDIA_DB[code])
    else:
        await update.message.reply_text("❌Bunday kod yo‘q!")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_media))
    app.add_handler(CallbackQueryHandler(check_sub_callback, pattern="check_sub"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_code))
    app.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO | filters.Document.ALL, save_media))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_media))

    app.run_polling()


if __name__ == "__main__":
    main()


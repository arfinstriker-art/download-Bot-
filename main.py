import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)

# 🔑 Render environment variable
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN missing! Render-এ add করো")

users = set()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)
    await update.message.reply_text(
        "👋 Welcome!\n\n📥 TikTok / Facebook / YouTube ভিডিও লিংক পাঠান"
    )

# stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👥 Total Users: {len(users)}")

# link handler
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "http" not in url:
        await update.message.reply_text("❌ সঠিক লিংক দিন")
        return

    context.user_data["url"] = url

    keyboard = [
        [InlineKeyboardButton("🎥 Video", callback_data="video")],
        [InlineKeyboardButton("🎵 Audio", callback_data="audio")]
    ]

    await update.message.reply_text(
        "📌 কী ডাউনলোড করতে চান?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# choice handler
async def choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "video":
        keyboard = [
            [InlineKeyboardButton("360p", callback_data="360")],
            [InlineKeyboardButton("720p", callback_data="720")]
        ]
        await query.edit_message_text(
            "🎥 Quality বেছে নিন:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "audio":
        await query.edit_message_text("🎵 Audio ডাউনলোড হচ্ছে...")
        await download(update, context, audio=True)

# quality handler
async def quality_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality = query.data
    await query.edit_message_text(f"⏳ {quality}p ডাউনলোড হচ্ছে...")

    await download(update, context, quality=quality)

# download function
async def download(update, context, quality=None, audio=False):
    url = context.user_data.get("url")
    chat_id = update.effective_chat.id

    try:
        await context.bot.send_message(chat_id, "📥 Processing...")

        if audio:
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': 'audio.%(ext)s',
                'quiet': True
            }
        else:
            if quality == "360":
                fmt = "bestvideo[height<=360]+bestaudio/best"
            else:
                fmt = "bestvideo[height<=720]+bestaudio/best"

            ydl_opts = {
                'format': fmt,
                'outtmpl': 'video.%(ext)s',
                'merge_output_format': 'mp4',
                'quiet': True
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        # send file
        if audio:
            await context.bot.send_audio(chat_id, audio=open(file_path, 'rb'))
        else:
            await context.bot.send_video(chat_id, video=open(file_path, 'rb'))

        os.remove(file_path)

        await context.bot.send_message(chat_id, "✅ Done!")

    except Exception as e:
        await context.bot.send_message(chat_id, "⚠️ Download failed!")

# main run
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(choice_handler, pattern="video|audio"))
app.add_handler(CallbackQueryHandler(quality_handler, pattern="360|720"))

print("🚀 Bot running...")
app.run_polling()

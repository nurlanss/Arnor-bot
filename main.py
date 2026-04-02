import os
import logging
import re
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from youtube_transcript_api import YouTubeTranscriptApi

# Настройки ключей
TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

logging.basicConfig(level=logging.INFO)

def extract_video_id(url):
    pattern = r'(?:v=|\/embed\/|\/watch\?v=|youtu\.be\/)([A-Za-z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пришли ссылку на YouTube, и я сделаю конспект через Gemini (бесплатно)!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vid = extract_video_id(update.message.text)
    if not vid:
        await update.message.reply_text("Пришли прямую ссылку на видео.")
        return

    m = await update.message.reply_text("⏳ Читаю субтитры...")
    
    try:
        ts = YouTubeTranscriptApi.get_transcript(vid, languages=['ru', 'en'])
        text = " ".join([x['text'] for x in ts])[:30000]

        await m.edit_text("✍️ Gemini анализирует текст...")
        
        response = model.generate_content(f"Сделай подробный конспект этого видео на русском языке с таймкодами: {text}")
        
        await update.message.reply_text(response.text)
        await m.delete()

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()

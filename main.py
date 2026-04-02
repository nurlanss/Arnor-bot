import os
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from youtube_transcript_api import YouTubeTranscriptApi
import anthropic

# Ключи подтянутся из настроек Render
TOKEN = os.getenv("BOT_TOKEN")
CLAUDE_KEY = os.getenv("CLAUDE_KEY")

client = anthropic.Anthropic(api_key=CLAUDE_KEY)
logging.basicConfig(level=logging.INFO)

def extract_video_id(url):
    pattern = r'(?:v=|\/embed\/|\/watch\?v=|youtu\.be\/)([A-Za-z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пришли ссылку на YouTube, и я сделаю структурированный конспект!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vid = extract_video_id(update.message.text)
    if not vid:
        await update.message.reply_text("Не могу найти ID видео в ссылке.")
        return

    m = await update.message.reply_text("⏳ Получаю транскрипт...")
    
    try:
        # Пытаемся найти русские, а затем английские субтитры
        transcript_list = YouTubeTranscriptApi.list_transcripts(vid)
        try:
            transcript = transcript_list.find_transcript(['ru'])
        except:
            transcript = transcript_list.find_transcript(['en'])
            
        data = transcript.fetch()
        text = " ".join([x['text'] for x in data])[:15000]

        await m.edit_text("✍️ Claude формирует конспект...")
        
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            system="Ты профессиональный аналитик. Сделай краткий и содержательный конспект видео на русском языке, разбив его на главы с таймкодами.",
            messages=[{"role": "user", "content": text}]
        )
        
        await update.message.reply_text(response.content[0].text)
        await m.delete()

    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {str(e)}")

def main():
    if not TOKEN:
        print("Ошибка: Переменная BOT_TOKEN не настроена!")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()

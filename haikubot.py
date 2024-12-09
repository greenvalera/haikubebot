import os
from dotenv import load_dotenv
from openai import OpenAI
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from telegram import Update

# Load environment variables from .env file
load_dotenv()

# Токени беруться з середовища
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI()

messages_buffer = []

async def handle_message(update: Update, context: CallbackContext):
    if update.message and update.message.text:
        text = update.message.text.strip()
    else:
        return
    
    if text:
        print(text)
        messages_buffer.append(text)
        if len(messages_buffer) == 20:
            prompt = "З цих повідомлень: " + "\n".join(messages_buffer) + "\nЗгенеруй хокку мовою цих повідомлень."
            completion = completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            haiku = completion.choices[0].message.content.strip()
            await update.message.reply_text(haiku)
            messages_buffer.clear()

if __name__ == "__main__":
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()


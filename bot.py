import os
import telebot
from flask import Flask, request

# Инициализируем токен бота из переменных окружения Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Создаем Flask-приложение для прослушивания вебхуков
app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "Бот работает!", 200

# Твои команды бота
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! Я твой MOEX бот. Скоро я буду присылать котировки!")

# Автоматическая привязка вебхука при старте сервера на Render
bot.remove_webhook()
bot.set_webhook(url="https://moex-bot123.onrender.com/" + TOKEN)

# Точка входа для локального запуска (Render запускает через gunicorn в обход этого блока)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


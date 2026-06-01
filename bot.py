import telebot
import requests
import time
import threading
from telebot import types
from flask import Flask

# Создаем веб-сервер для обмана "спящего режима" хостинга
app = Flask('')

@app.route('/')
def home():
    return "Бот работает 24/7!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

TOKEN = "8919949961:AAEOUBv5dkqLuP0ArTOy6vGfRt_45Xqh988"
bot = telebot.TeleBot(TOKEN)

DEPOSIT = 10000.0

TARGETS = {
    'MAM6':       {'desc': 'Мини-Индекс',  'lots': 4, 'margin': 2200},
    'CRM6':       {'desc': 'Мини-Юань',    'lots': 3, 'margin': 2700},
    'BRM6':       {'desc': 'Нефть Brent',   'lots': 3, 'margin': 3000},
    'NGM6':       {'desc': 'Природный газ', 'lots': 3, 'margin': 2700},
    'GOLD-6.26':  {'desc': 'Золото',        'lots': 3, 'margin': 3000},
    'SILV-6.26':  {'desc': 'Серебро',       'lots': 4, 'margin': 2400},
    'SiM6':       {'desc': 'Доллар/Рубль',  'lots': 2, 'margin': 5000}
}

last_statuses = {ticker: "⏳ ЖДЕМ" for ticker in TARGETS}

def get_moex_data(ticker):
    try:
        url = f"https://iss.moex.com/iss/engines/futures/markets/forts/securities/{ticker}.json"
        response = requests.get(url, timeout=5)
        data = response.json()
        rows = data['marketdata']['data']
        columns = data['marketdata']['columns']
        last_idx = columns.index('LAST')
        change_idx = columns.index('LASTTOPREVPRICE')
        if rows and rows[0][last_idx] is not None:
            return rows[0][last_idx], rows[0][change_idx]
    except Exception:
        pass
    return None, None

def analyze_15m_trend(change):
    if change is None: return "⏳ ЖДЕМ"
    if change > 0.8: return "🟢 ПОКУПКА"
    elif change < -0.8: return "🔴 ПРОДАЖА"
    return "⏳ ЖДЕМ"

# Функция сканирования рынка каждые 30 минут (1800 секунд)
def scan_market(chat_id):
    while True:
        for ticker, info in TARGETS.items():
            price, change = get_moex_data(ticker)
            current_status = analyze_15m_trend(change)
            
            if current_status != last_statuses[ticker]:
                if current_status in ["🟢 ПОКУПКА", "🔴 ПРОДАЖА"]:
                    price_str = f"{price}" if price else "Нет данных"
                    change_str = f"{change:+.2f}%" if change else "0.00%"
                    total_item_margin = info['margin'] * info['lots']
                    
                    msg = f"🚨 *СИГНАЛ НА РЫНКЕ!*\n\n🔹 *{ticker}* ({info['desc']})\n• Действие: {current_status}\n• Цена: {price_str} ({change_str})\n• Заход на все 10к: *{info['lots']} лот*"
                    try:
                        bot.send_message(chat_id, msg, parse_mode="Markdown")
                    except Exception:
                        pass
                last_statuses[ticker] = current_status
        time.sleep(1800) # Проверка каждые 30 минут

def build_status_message():
    lines = []
    for ticker, info in TARGETS.items():
        price, change = get_moex_data(ticker)
        status = analyze_15m_trend(change)
        total_item_margin = info['margin'] * info['lots']
        pnl = total_item_margin * (change / 100.0) if change else 0.0
        
        price_str = f"{price}" if price else "Нет данных"
        change_str = f"{change:+.2f}%" if change else "0.00%"
        
        if pnl > 0: pnl_str = f"🟢 Результат: +{pnl:.1f}₽"
        elif pnl < 0: pnl_str = f"🔴 Результат: {pnl:.1f}₽"
        else: pnl_str = "⚪️ По нулям"
            
        lines.append(f"🔹 *{ticker}* ({info['desc']})\n• {status} | Цена: {price_str} ({change_str})\n• Покупка на все 10к: *{info['lots']} лот*\n• {pnl_str}\n")
    
    header = f"💰 *ТВОЙ ДЕПОЗИТ:* {DEPOSIT:,.0f} руб.\n"
    return header + "-----------------------------------------\n\n" + "\n".join(lines)

@bot.message_handler(commands=['start', 'go'])
def start_monitoring(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📈 Показать все варианты"))
    bot.send_message(message.chat.id, "🤖 Авто-мониторинг 24/7 запущен на сервере! Проверка каждые 30 минут.", reply_markup=markup)
    # Запускаем фоновый поток для проверки рынка
    threading.Thread(target=scan_market, args=(message.chat.id,), daemon=True).start()

@bot.message_handler(func=lambda message: message.text == "📈 Показать все варианты")
def show_all_variants(message):
    bot.send_message(message.chat.id, build_status_message(), parse_mode="Markdown")

if __name__ == "__main__":
    # Запускаем веб-сервер в отдельном потоке
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.polling(none_stop=True)

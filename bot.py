import os
import json
import logging
from flask import Flask, request, jsonify
import telebot
from telebot.types import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# 🔧 НАСТРОЙКИ
BOT_TOKEN = "ТВОЙ_ТОКЕН_СЮДА"
YOUR_TELEGRAM_ID = 985380350
PORT = int(os.getenv("PORT", 8000))

WEB_APP_URL = "https://football-dreamteam.onrender.com/index.html"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# =========================
# 🔥 WEBHOOK
# =========================
@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("🔥 ПОЛУЧЕН ВЕБХУК")

    update_json = request.get_json()
    logger.info(f"Update: {update_json}")

    # 👉 ЛОВИМ WEB APP DATA
    if 'message' in update_json and 'web_app_data' in update_json['message']:
        logger.info("📦 ПОЛУЧЕНЫ ДАННЫЕ ИЗ WEB APP")

        raw_data = update_json['message']['web_app_data']['data']
        logger.info(f"RAW DATA: {raw_data}")

        try:
            order = json.loads(raw_data)

            team = order.get("team", "Не указана")
            customer = order.get("customer", {})
            players = order.get("players", [])

            # 📩 Формируем сообщение
            text = f"🆕 *НОВЫЙ ЗАКАЗ!*\n\n"
            text += f"*Команда:* {team}\n\n"

            text += f"*Клиент:*\n"
            text += f"Фамилия: {customer.get('surname', '')}\n"
            text += f"Имя: {customer.get('name', '')}\n"
            text += f"Отчество: {customer.get('patronymic', '')}\n"
            text += f"Телефон: {customer.get('phone', '')}\n"
            text += f"Адрес: {customer.get('address', '')}\n\n"

            text += "*Состав:*\n"
            for p in players:
                text += f"{p['position']}: {p['name']}\n"

            # 📤 Отправляем тебе
            bot.send_message(YOUR_TELEGRAM_ID, text)
            logger.info("✅ Отправлено администратору")

            # 📤 Ответ пользователю
            chat_id = update_json['message']['chat']['id']
            bot.send_message(chat_id, "✅ Заказ получен! Спасибо!")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки JSON: {e}")

    # 👉 Обрабатываем остальные апдейты
    update = Update.de_json(update_json)
    bot.process_new_updates([update])

    return jsonify({'ok': True})


# =========================
# 🟢 /start С КНОПКОЙ
# =========================
@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"/start от {message.from_user.id}")

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            text="⚽ Собрать состав",
            web_app=WebAppInfo(WEB_APP_URL)
        )
    )

    bot.send_message(
        message.chat.id,
        "Собери свой состав мечты 👇",
        reply_markup=markup
    )


# =========================
# 🔍 HEALTH CHECK
# =========================
@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200


# =========================
# 🚀 ЗАПУСК
# =========================
if __name__ == "__main__":
    webhook_url = "https://football-dreamteam.onrender.com/webhook"

    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)

    logger.info(f"✅ Вебхук установлен: {webhook_url}")

    app.run(host='0.0.0.0', port=PORT)

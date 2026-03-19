import os
import json
import logging
import asyncio
from flask import Flask, request, jsonify
import telebot
from telebot.types import Update

# Настройки
BOT_TOKEN = "8523781397:AAES_yF9SIUwUqAIQVVC99bhDDIVAIFSYKE"
YOUR_TELEGRAM_ID = 985380350
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("🔥 Получен вебхук")
    update = request.get_json()
    logger.info(f"Update: {update}")
    
    # Передаём обновление боту
    update = Update.de_json(update)
    bot.process_new_updates([update])
    
    return jsonify({'ok': True}), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check для Render"""
    return 'OK', 200

# Обработчики команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    logger.info(f"Команда /start от {message.from_user.id}")
    bot.reply_to(
        message,
        "Привет! Это бот для приёма заказов из мини-приложения.\n"
        "Заполни состав в приложении, нажми «Подтвердить» — данные придут сюда."
    )

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    logger.info("🔥 ПОЛУЧЕН WEB_APP_DATA")
    logger.info(f"Данные: {message.web_app_data.data}")

    data = message.web_app_data.data
    try:
        order = json.loads(data)
    except json.JSONDecodeError:
        bot.reply_to(message, "Ошибка: не удалось разобрать данные.")
        return

    team = order.get("team", "Не указана")
    customer = order.get("customer", {})
    players = order.get("players", [])

    text = f"🆕 **Новый заказ!**\n\n"
    text += f"**Команда:** {team}\n\n"
    text += f"**Клиент:**\n"
    text += f"Фамилия: {customer.get('surname', '')}\n"
    text += f"Имя: {customer.get('name', '')}\n"
    text += f"Отчество: {customer.get('patronymic', '')}\n"
    text += f"Телефон: {customer.get('phone', '')}\n"
    text += f"Адрес: {customer.get('address', '')}\n\n"
    text += f"**Состав:**\n"
    for p in players:
        text += f"{p['position']}: {p['name']}\n"

    bot.send_message(YOUR_TELEGRAM_ID, text)
    bot.reply_to(message, "Спасибо! Ваш заказ принят.")

@bot.message_handler(func=lambda message: True)
def handle_other(message):
    logger.debug(f"Другое сообщение: {message.content_type}")

if __name__ == "__main__":
    # Устанавливаем вебхук при запуске
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info(f"Вебхук установлен на {webhook_url}")
    
    # Запускаем Flask-сервер
    app.run(host='0.0.0.0', port=PORT)

import os
import json
import logging
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
    logger.info("🔥 ПОЛУЧЕН ВЕБХУК")
    update_json = request.get_json()
    logger.info(f"Update: {update_json}")
    
    # Преобразуем JSON в объект Update
    update = Update.de_json(update_json)
    
    # Проверяем наличие web_app_data
    if update.message and update.message.web_app_data:
        logger.info("📦 ЭТО WEB_APP_DATA!")
        logger.info(f"Данные: {update.message.web_app_data.data}")
        
        # Обрабатываем данные
        data = update.message.web_app_data.data
        try:
            order = json.loads(data)
            logger.info(f"Распарсенный JSON: {order}")
            
            # Формируем сообщение
            if order.get('test'):
                text = f"✅ ТЕСТОВЫЕ ДАННЫЕ ПОЛУЧЕНЫ!\nВремя: {order.get('time')}"
            else:
                team = order.get("team", "Не указана")
                customer = order.get("customer", {})
                players = order.get("players", [])
                
                text = f"🆕 **НОВЫЙ ЗАКАЗ!**\n\n"
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
            
            # Отправляем вам
            bot.send_message(YOUR_TELEGRAM_ID, text)
            logger.info("✅ Сообщение отправлено администратору")
            
            # Подтверждаем пользователю
            bot.send_message(update.message.chat.id, "Спасибо! Ваш заказ принят.")
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки: {e}")
    
    # Передаем обновление боту для обработки других команд
    bot.process_new_updates([update])
    
    return jsonify({'ok': True}), 200

@app.route('/health', methods=['GET'])
def health():
    return 'OK', 200

@bot.message_handler(commands=['start'])
def handle_start(message):
    logger.info(f"Команда /start от {message.from_user.id}")
    bot.reply_to(
        message,
        "Привет! Это бот для приёма заказов из мини-приложения.\n"
        "Заполни состав в приложении, нажми «Подтвердить» — данные придут сюда."
    )

@bot.message_handler(func=lambda message: True)
def handle_other(message):
    logger.debug(f"Другое сообщение: {message.text}")

if __name__ == "__main__":
    # Устанавливаем вебхук
    webhook_url = f"https://football-dreamteam.onrender.com/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Вебхук установлен на {webhook_url}")
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=PORT)

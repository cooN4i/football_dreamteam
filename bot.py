import os
import json
import logging
from flask import Flask, request, jsonify
import telebot
from telebot.types import Update

# ---------------- CONFIG ----------------
TOKEN = "8523781397:AAES_yF9SIUwUqAIQVVC99bhDDIVAIFSYKE"  # токен лучше хранить в переменных окружения
WEBHOOK_URL = "https://football-dreamteam.onrender.com/webhook"

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- WEBHOOK ----------------
@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("🔥 ПОЛУЧЕН ВЕБХУК")

    # ВАЖНО: silent=True чтобы не падал с 400
    update_json = request.get_json(silent=True)

    if not update_json:
        logger.warning("⚠️ Пустой или невалидный JSON")
        return jsonify({'ok': True})

    logger.info(f"📩 Update: {update_json}")

    # ---------------- WEB APP DATA ----------------
    if 'message' in update_json and 'web_app_data' in update_json['message']:
        logger.info("📦 ПОЛУЧЕНЫ ДАННЫЕ ИЗ WEB APP")

        try:
            raw_data = update_json['message']['web_app_data']['data']
            logger.info(f"RAW DATA: {raw_data}")

            data = json.loads(raw_data)

            chat_id = update_json['message']['chat']['id']

            # Пример обработки
            bot.send_message(chat_id, "✅ Заказ получен!")

            # Можно отправить администратору
            ADMIN_CHAT_ID = 985380350

            if ADMIN_CHAT_ID:
                bot.send_message(
                    ADMIN_CHAT_ID,
                    f"📦 Новый заказ:\n\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                )

        except Exception as e:
            logger.error(f"❌ Ошибка обработки web_app_data: {e}")

    # ---------------- TELEGRAM UPDATES ----------------
    try:
        update = Update.de_json(update_json)
        bot.process_new_updates([update])
    except Exception as e:
        logger.error(f"❌ Ошибка process_new_updates: {e}")

    return jsonify({'ok': True})


# ---------------- START COMMAND ----------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Бот работает ✅")


# ---------------- HEALTHCHECK ----------------
@app.route('/health', methods=['GET'])
def health():
    return "OK", 200


# ---------------- WEBHOOK SETUP ----------------
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    logger.info("✅ Webhook установлен")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    set_webhook()

    # Render требует bind на 0.0.0.0
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

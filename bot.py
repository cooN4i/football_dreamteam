import os
import json
import logging
from flask import Flask, request, jsonify
import telebot
from telebot.types import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# ---------------- CONFIG ----------------
TOKEN = "8523781397:AAES_yF9SIUwUqAIQVVC99bhDDIVAIFSYKE"  # лучше вынести в env
WEBHOOK_URL = "https://football-dreamteam.onrender.com/webhook"

ADMIN_CHAT_ID = 985380350

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- WEBHOOK ----------------
@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("🔥 ПОЛУЧЕН ВЕБХУК")

    update_json = request.get_json(silent=True)

    if not update_json:
        logger.warning("⚠️ Пустой JSON")
        return jsonify({'ok': True})

    logger.info(f"📩 Update: {update_json}")

    # ---------------- WEB APP DATA ----------------
    if 'message' in update_json and 'web_app_data' in update_json['message']:
        logger.info("📦 WEB APP DATA ПОЛУЧЕНЫ")

        try:
            raw_data = update_json['message']['web_app_data']['data']
            data = json.loads(raw_data)

            chat_id = update_json['message']['chat']['id']

            # Ответ пользователю
            bot.send_message(chat_id, "✅ Заказ получен!")

            # ---------------- КРАСИВОЕ ФОРМИРОВАНИЕ ----------------
            order_id = data.get("order_id", "—")
            team = data.get("team", "—")
            customer = data.get("customer", {})
            players = data.get("players", [])

            customer_text = (
                f"{customer.get('surname', '')} "
                f"{customer.get('name', '')} "
                f"{customer.get('patronymic', '')}"
            ).strip()

            players_text = "\n".join(
                [f"• {p.get('position')}: {p.get('name')}" for p in players]
            )

            message_text = (
                f"📦 <b>Новый заказ №{order_id}</b>\n\n"
                f"⚽ <b>Команда:</b> {team}\n\n"
                f"👤 <b>Клиент:</b>\n"
                f"{customer_text}\n"
                f"📞 {customer.get('phone', '—')}\n"
                f"📍 {customer.get('address', '—')}\n\n"
                f"🧩 <b>Состав:</b>\n"
                f"{players_text}"
            )

            # Отправка админу
            if ADMIN_CHAT_ID:
                bot.send_message(
                    ADMIN_CHAT_ID,
                    message_text,
                    parse_mode="HTML"
                )

        except Exception as e:
            logger.error(f"❌ Ошибка обработки: {e}")

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
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    web_app = WebAppInfo(url="https://coon4i.github.io/football_dreamteam/")

    button = KeyboardButton(text="⚽ Открыть конструктор", web_app=web_app)
    markup.add(button)

    bot.send_message(
        message.chat.id,
        "Нажми кнопку ниже 👇",
        reply_markup=markup
    )


# ---------------- HEALTH ----------------
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

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
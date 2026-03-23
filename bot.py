import os
import json
import logging
from flask import Flask, request, jsonify
import telebot
from telebot.types import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# ---------------- CONFIG ----------------
TOKEN = "8778825702:AAGI0zTcL4zOGdlrJ5HuTKdT5as_SJE_D90"
WEBHOOK_URL = "https://football-dreamteam.onrender.com/webhook"
ADMIN_CHAT_ID = 985380350

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🚀 BOT STARTED")

# ---------------- WEBHOOK ----------------


@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("🔥 WEBHOOK HIT")

    try:
        update_json = request.get_json()

        logger.info("📥 RAW UPDATE:")
        logger.info(json.dumps(update_json, indent=2, ensure_ascii=False))

        update = Update.de_json(update_json)
        bot.process_new_updates([update])

        logger.info("✅ Update processed")

    except Exception as e:
        logger.exception(f"❌ WEBHOOK ERROR: {e}")

    return jsonify({'ok': True})


# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    logger.info("📩 /start received")

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    web_app_button = KeyboardButton(
        text="⚽ Открыть конструктор",
        web_app=WebAppInfo(
            url="https://coon4i.github.io/football_dreamteam/"
        )
    )

    markup.add(web_app_button)

    bot.send_message(
        message.chat.id,
        "Нажми кнопку ниже 👇",
        reply_markup=markup
    )

    logger.info("✅ Reply keyboard sent")


# ---------------- DEBUG ANY MESSAGE ----------------
@bot.message_handler(func=lambda m: True)
def debug_all(message):
    logger.info("📩 ANY MESSAGE RECEIVED")
    logger.info(message)


# ---------------- WEB APP DATA HANDLER ----------------
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app(message):
    logger.info("🔥 WEB_APP_DATA RECEIVED")

    try:
        raw_data = message.web_app_data.data
        logger.info(f"RAW DATA: {raw_data}")

        data = json.loads(raw_data)

        logger.info("📦 PARSED DATA:")
        logger.info(json.dumps(data, indent=2, ensure_ascii=False))

        chat_id = message.chat.id

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

        admin_message = (
            f"📦 <b>Новый заказ №{order_id}</b>\n\n"
            f"⚽ <b>Команда:</b> {team}\n\n"
            f"👤 <b>Клиент:</b>\n"
            f"{customer_text}\n"
            f"📞 {customer.get('phone', '—')}\n"
            f"📍 {customer.get('address', '—')}\n\n"
            f"🧩 <b>Состав:</b>\n"
            f"{players_text}"
        )

        logger.info("📨 Sending admin message...")
        bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
        logger.info("✅ Admin message sent")

        logger.info("📨 Sending user message...")
        bot.send_message(
            chat_id,
            f"✅ Заказ №{order_id} принят",
            parse_mode="HTML"
        )
        logger.info("✅ User message sent")

    except Exception as e:
        logger.exception(f"❌ WEB APP HANDLER ERROR: {e}")


# ---------------- HEALTH ----------------
@app.route('/health', methods=['GET'])
def health():
    return "OK", 200


# ---------------- WEBHOOK SET ----------------
def set_webhook():
    logger.info("🔧 Setting webhook...")

    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    logger.info("✅ Webhook set")

    logger.info(bot.get_webhook_info())


# ---------------- MAIN ----------------
if __name__ == "__main__":
    set_webhook()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

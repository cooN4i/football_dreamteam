import os
import json
import logging
from flask import Flask, request, jsonify
import telebot
from telebot.types import Update, InlineKeyboardMarkup, InlineKeyboardButton

# ---------------- CONFIG ----------------
TOKEN = "8778825702:AAGI0zTcL4zOGdlrJ5HuTKdT5as_SJE_D90"
WEBHOOK_URL = "https://football-dreamteam.onrender.com/webhook"
ADMIN_CHAT_ID = 985380350

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- STARTUP DEBUG ----------------
logger.info("🚀 BOT STARTING...")
logger.info(f"WEBHOOK URL: {WEBHOOK_URL}")
logger.info(f"ADMIN CHAT ID: {ADMIN_CHAT_ID}")

# ---------------- WEBHOOK INFO CHECK ----------------


def print_webhook_info():
    info = bot.get_webhook_info()
    logger.info("📡 WEBHOOK INFO:")
    logger.info(info)

# ---------------- WEBHOOK ----------------


@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("🔥🔥🔥 WEBHOOK HIT 🔥🔥🔥")

    try:
        update_json = request.get_json()

        logger.info("📥 RAW UPDATE JSON:")
        logger.info(json.dumps(update_json, indent=2, ensure_ascii=False))

        if not update_json:
            logger.warning("⚠️ Empty update_json")
            return jsonify({'ok': True})

        # Проверяем структуру
        logger.info(f"UPDATE KEYS: {list(update_json.keys())}")

        # Парсим update через telebot
        update = Update.de_json(update_json)

        logger.info("🔄 Parsed Update object created")

        # Передаём в telebot
        bot.process_new_updates([update])

        logger.info("✅ Update passed to bot.process_new_updates")

    except Exception as e:
        logger.exception(f"❌ WEBHOOK ERROR: {e}")

    return jsonify({'ok': True})


# ---------------- START COMMAND ----------------
@bot.message_handler(commands=['start'])
def start(message):
    logger.info("📩 /start command received")

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "⚽ Открыть конструктор",
            web_app=telebot.types.WebAppInfo(
                url="https://coon4i.github.io/football_dreamteam/"
            )
        )
    )

    bot.send_message(
        message.chat.id,
        "Нажми кнопку ниже 👇",
        reply_markup=markup
    )

    logger.info("✅ /start reply sent")


# ---------------- DEBUG: ANY MESSAGE ----------------
@bot.message_handler(func=lambda m: True)
def debug_all(message):
    logger.info("📩 ANY MESSAGE RECEIVED")
    logger.info(message)


# ---------------- WEB APP HANDLER ----------------
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app(message):
    logger.info("🔥🔥🔥 WEB_APP_DATA HANDLER TRIGGERED 🔥🔥🔥")

    try:
        raw_data = message.web_app_data.data
        logger.info(f"RAW WEB APP DATA: {raw_data}")

        data = json.loads(raw_data)

        logger.info("📦 PARSED DATA:")
        logger.info(json.dumps(data, indent=2, ensure_ascii=False))

        chat_id = message.chat.id

        order_id = data.get("order_id")
        team = data.get("team")
        customer = data.get("customer", {})
        players = data.get("players", [])

        logger.info(f"ORDER ID: {order_id}")
        logger.info(f"TEAM: {team}")
        logger.info(f"CUSTOMER: {customer}")
        logger.info(f"PLAYERS COUNT: {len(players)}")

        # Формируем текст
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
            f"📞 {customer.get('phone')}\n"
            f"📍 {customer.get('address')}\n\n"
            f"🧩 <b>Состав:</b>\n"
            f"{players_text}"
        )

        logger.info("📨 Sending message to admin...")

        bot.send_message(
            ADMIN_CHAT_ID,
            admin_message,
            parse_mode="HTML"
        )

        logger.info("✅ Admin message sent")

        logger.info("📨 Sending message to user...")

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
    logger.info("💚 HEALTH CHECK HIT")
    return "OK", 200


# ---------------- WEBHOOK SET ----------------
def set_webhook():
    logger.info("🔧 Setting webhook...")

    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    logger.info("✅ Webhook set")

    print_webhook_info()


# ---------------- MAIN ----------------
if __name__ == "__main__":
    set_webhook()

    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🚀 Starting Flask on port {port}")

    app.run(host="0.0.0.0", port=port)

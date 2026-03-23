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

# ---------------- WEBHOOK ----------------


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update_json = request.get_json()
        update = Update.de_json(update_json)
        bot.process_new_updates([update])
    except Exception as e:
        logger.exception(f"WEBHOOK ERROR: {e}")

    return jsonify({'ok': True})


# ---------------- START ----------------
@bot.message_handler(commands=['start'])
def start(message):
    from telebot.types import WebAppInfo

    markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url="https://coon4i.github.io/football_dreamteam/")

    markup.add(
        InlineKeyboardButton("⚽ Открыть конструктор", web_app=web_app)
    )

    bot.send_message(
        message.chat.id,
        "Нажми кнопку ниже 👇",
        reply_markup=markup
    )


# ---------------- WEB APP HANDLER ----------------
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app(message):
    try:
        data = json.loads(message.web_app_data.data)

        logger.info(f"WEB APP DATA: {data}")

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

        tg_username = customer.get("telegram")
        tg_id = customer.get("telegram_id")

        if tg_username:
            telegram_display = f"@{tg_username}"
        elif tg_id:
            telegram_display = f"id: {tg_id}"
        else:
            telegram_display = "не указан"

        players_text = "\n".join(
            [f"• {p.get('position')}: {p.get('name')}" for p in players]
        )

        # -------- ADMIN MESSAGE --------
        admin_message = (
            f"📦 <b>Новый заказ №{order_id}</b>\n\n"
            f"⚽ <b>Команда:</b> {team}\n\n"
            f"👤 <b>Клиент:</b>\n"
            f"{customer_text}\n"
            f"📱 Telegram: {telegram_display}\n"
            f"📞 {customer.get('phone', '—')}\n"
            f"📍 {customer.get('address', '—')}\n\n"
            f"🧩 <b>Состав:</b>\n"
            f"{players_text}"
        )

        admin_markup = InlineKeyboardMarkup()

        if tg_username:
            admin_markup.add(
                InlineKeyboardButton(
                    "💬 Написать клиенту",
                    url=f"https://t.me/{tg_username}"
                )
            )

        bot.send_message(
            ADMIN_CHAT_ID,
            admin_message,
            parse_mode="HTML",
            reply_markup=admin_markup
        )

        # -------- USER MESSAGE --------
        user_markup = InlineKeyboardMarkup()
        user_markup.add(
            InlineKeyboardButton(
                "📩 Написать в поддержку",
                url="https://t.me/kylo_gg"
            )
        )

        bot.send_message(
            chat_id,
            f"✅ <b>Спасибо за заказ!</b>\n\n📦 Заказ №{order_id}",
            parse_mode="HTML",
            reply_markup=user_markup
        )

    except Exception as e:
        logger.exception(f"WEB APP HANDLER ERROR: {e}")


# ---------------- HEALTH ----------------
@app.route('/health', methods=['GET'])
def health():
    return "OK", 200


# ---------------- WEBHOOK SET ----------------
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    logger.info("✅ Webhook set")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    set_webhook()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

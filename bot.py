import os
import json
import logging
from flask import Flask, request, jsonify
import telebot
from telebot.types import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# ---------------- CONFIG ----------------
TOKEN = "8523781397:AAES_yF9SIUwUqAIQVVC99bhDDIVAIFSYKE"
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
    logger.info("🔥 WEBHOOK RECEIVED")

    update_json = request.get_json(silent=True)

    if not update_json:
        return jsonify({'ok': True})

    # -------- WEBAPP DATA --------
    if 'message' in update_json and 'web_app_data' in update_json['message']:
        try:
            raw_data = update_json['message']['web_app_data']['data']
            data = json.loads(raw_data)

            chat_id = update_json['message']['chat']['id']

            order_id = data.get("order_id", "—")
            team = data.get("team", "—")
            customer = data.get("customer", {})
            players = data.get("players", [])

            # клиент
            customer_text = (
                f"{customer.get('surname', '')} "
                f"{customer.get('name', '')} "
                f"{customer.get('patronymic', '')}"
            ).strip()

            # telegram username
            tg_username = customer.get("telegram", None)
            tg_id = customer.get("telegram_id", None)

            telegram_line = tg_username if tg_username else "не указан"
            telegram_id_line = tg_id if tg_id else "не указан"

            # игроки
            players_text = "\n".join(
                [f"• {p.get('position')}: {p.get('name')}" for p in players]
            )

            # сообщение админу
            admin_message = (
                f"📦 <b>Новый заказ №{order_id}</b>\n\n"
                f"⚽ <b>Команда:</b> {team}\n\n"
                f"👤 <b>Клиент:</b>\n"
                f"{customer_text}\n"
                f"📱 Telegram: {telegram_line}\n"
                f"🆔 ID: {telegram_id_line}\n"
                f"📞 {customer.get('phone', '—')}\n"
                f"📍 {customer.get('address', '—')}\n\n"
                f"🧩 <b>Состав:</b>\n"
                f"{players_text}"
            )

            # отправка админу
            if ADMIN_CHAT_ID:
                bot.send_message(
                    ADMIN_CHAT_ID,
                    admin_message,
                    parse_mode="HTML"
                )

            # отправка пользователю
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("📩 Написать в поддержку", url="https://t.me/kylo_gg")
            )

            bot.send_message(
                chat_id,
                f"✅ <b>Спасибо за заказ!</b>\n\n"
                f"📦 Номер заказа: <b>№{order_id}</b>\n\n"
                f"📝 Если есть вопросы - напишите нам.",
                parse_mode="HTML",
                reply_markup=markup
            )

        except Exception as e:
            logger.error(f"❌ Error: {e}")

    # обработка обычных апдейтов
    try:
        update = Update.de_json(update_json)
        bot.process_new_updates([update])
    except Exception as e:
        logger.error(f"❌ Update error: {e}")

    return jsonify({'ok': True})


# ---------------- START ----------------
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
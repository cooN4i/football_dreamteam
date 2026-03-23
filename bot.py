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
    logger.info("🔥 WEBHOOK RECEIVED")

    update_json = request.get_json(silent=True)
    logger.info(f"📦 Full update_json: {update_json}")  # ← добавили

    if not update_json:
        return jsonify({'ok': True})

    # -------- WEBAPP DATA --------
    # Проверяем наличие web_app_data как в сообщении, так и в callback_query (на всякий случай)
    web_app_data = None
    chat_id = None

    if 'message' in update_json and 'web_app_data' in update_json['message']:
        web_app_data = update_json['message']['web_app_data']['data']
        chat_id = update_json['message']['chat']['id']
        logger.info(f"✅ Найдено web_app_data в message")
    elif 'callback_query' in update_json and 'message' in update_json['callback_query'] and 'web_app_data' in update_json['callback_query']['message']:
        # редко, но для полноты
        web_app_data = update_json['callback_query']['message']['web_app_data']['data']
        chat_id = update_json['callback_query']['message']['chat']['id']
        logger.info(f"✅ Найдено web_app_data в callback_query")

    if web_app_data:
        try:
            data = json.loads(web_app_data)
            logger.info(f"📊 Распарсенные данные: {data}")

            order_id = data.get("order_id", "—")
            order_date = data.get("order_date", "—")
            team = data.get("team", "—")
            customer = data.get("customer", {})
            players = data.get("players", [])

            # Надёжное получение TG данных
            from_user = update_json.get('message', {}).get('from', {})
            tg_id = customer.get("telegram_id") or chat_id
            tg_username = customer.get("telegram")
            if not tg_username and from_user.get("username"):
                tg_username = "@" + from_user.get("username")

            customer_text = (
                f"{customer.get('surname', '')} "
                f"{customer.get('name', '')} "
                f"{customer.get('patronymic', '')}"
            ).strip()

            telegram_line = tg_username if tg_username else "не указан"
            telegram_id_line = tg_id if tg_id else "не указан"

            players_text = "\n".join(
                [f"• {p.get('position')}: {p.get('name')}" for p in players]
            )

            admin_message = (
                f"📦 <b>Новый заказ №{order_id}</b>\n\n"
                f"📅 <b>Дата заказа:</b> {order_date}\n\n"
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

            if ADMIN_CHAT_ID:
                bot.send_message(
                    ADMIN_CHAT_ID,
                    admin_message,
                    parse_mode="HTML"
                )
                logger.info(f"✅ Отправлено админу: №{order_id}")

            # отправка пользователю
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton(
                    "📩 Написать в поддержку", url="https://t.me/kylo_gg")
            )

            bot.send_message(
                chat_id,
                f"✅ <b>Спасибо за заказ!</b>\n\n"
                f"📦 Номер заказа: <b>№{order_id}</b>\n\n"
                f"📝 Если есть вопросы - напишите нам.",
                parse_mode="HTML",
                reply_markup=markup
            )
            logger.info(f"✅ Отправлено пользователю {chat_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка обработки web_app_data: {e}")

    # обработка обычных апдейтов (команды и т.п.)
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
        "Нажмите кнопку ниже 👇",
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

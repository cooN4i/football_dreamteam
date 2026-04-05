import os
import json
import logging
import requests
from flask import Flask, request, jsonify
import telebot
from telebot.types import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
)

# ---------------- CONFIG ----------------
TOKEN = "8778825702:AAGI0zTcL4zOGdlrJ5HuTKdT5as_SJE_D90"
WEBHOOK_URL = "https://football-dreamteam.onrender.com/webhook"
ADMIN_CHAT_ID = 985380350

# === ДАННЫЕ Т-БАНКА ===
TERMINAL_KEY = "1775395377330DEMO"          # ← ОБЯЗАТЕЛЬНО ЗАМЕНИ
# ← ОБЯЗАТЕЛЬНО ЗАМЕНИ (Secret Key / Пароль терминала)
PASSWORD = "8GpcH_i4V!&j$4nb"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------- ИНИЦИАЦИЯ ПЛАТЕЖА ----------------
@app.route('/init-payment', methods=['POST'])
def init_payment():
    try:
        data = request.get_json()
        order_id = data.get("orderId")
        amount = data.get("amount")          # в копейках
        description = data.get("description", f"Заказ №{order_id}")

        if not order_id or not amount:
            return jsonify({"error": "Нет orderId или amount"}), 400

        payload = {
            "TerminalKey": TERMINAL_KEY,
            "Amount": amount,
            "OrderId": str(order_id),
            "Description": description,
            "NotificationURL": "https://football-dreamteam.onrender.com/payment-notification",
            "SuccessURL": "https://t.me/твойбот?start=success",
            "FailURL": "https://t.me/твойбот?start=fail",
            "DATA": {"Phone": data.get("customer", {}).get("phone", "")}
        }

        response = requests.post(
            "https://securepay.tinkoff.ru/v2/Init", json=payload, timeout=15)
        result = response.json()

        logger.info(f"T-Bank Init ответ: {result}")

        if result.get("Success") and result.get("PaymentURL"):
            return jsonify({"PaymentURL": result["PaymentURL"]})
        else:
            error = result.get("Message") or result.get(
                "Details") or "Неизвестная ошибка Т-Банка"
            return jsonify({"error": error}), 400

    except Exception as e:
        logger.error(f"Ошибка /init-payment: {e}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500


# ---------------- УВЕДОМЛЕНИЕ ОПЛАТЫ ----------------
@app.route('/payment-notification', methods=['POST'])
def payment_notification():
    try:
        data = request.get_json() or dict(request.form)
        logger.info(f"Уведомление от Т-Банка: {data}")

        if data.get("Status") == "CONFIRMED":
            order_id = data.get("OrderId")
            logger.info(f"✅ Оплата прошла! Заказ №{order_id}")
            # Здесь можно отправить доп. сообщение админу

        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")
        return "OK", 200


# ---------------- ТВОЙ СТАРЫЙ WEBHOOK ----------------
@app.route('/webhook', methods=['POST'])
def webhook():
    logger.info("🔥 WEBHOOK RECEIVED")
    update_json = request.get_json(silent=True)
    if not update_json:
        return jsonify({'ok': True})

    web_app_data = None
    chat_id = None
    if 'message' in update_json and 'web_app_data' in update_json['message']:
        web_app_data = update_json['message']['web_app_data']['data']
        chat_id = update_json['message']['chat']['id']
    elif 'callback_query' in update_json and 'message' in update_json['callback_query'] and 'web_app_data' in update_json['callback_query']['message']:
        web_app_data = update_json['callback_query']['message']['web_app_data']['data']
        chat_id = update_json['callback_query']['message']['chat']['id']

    if web_app_data:
        try:
            data = json.loads(web_app_data)
            order_id = data.get("order_id", "—")
            order_date = data.get("order_date", "—")
            team = data.get("team", "—")
            customer = data.get("customer", {})
            players = data.get("players", [])

            from_user = update_json.get('message', {}).get('from', {})
            tg_id = customer.get("telegram_id") or chat_id
            tg_username = customer.get("telegram")
            if not tg_username and from_user.get("username"):
                tg_username = "@" + from_user.get("username")

            customer_text = f"{customer.get('surname', '')} {customer.get('name', '')} {customer.get('patronymic', '')}".strip(
            )
            telegram_line = tg_username if tg_username else "не указан"
            telegram_id_line = tg_id if tg_id else "не указан"
            players_text = "\n".join(
                [f"• {p.get('position')}: {p.get('name')}" for p in players])

            admin_message = (
                f"📦 <b>Новый заказ №{order_id}</b>\n\n"
                f"📅 <b>Дата заказа:</b> {order_date}\n\n"
                f"⚽ <b>Команда:</b> {team}\n\n"
                f"👤 <b>Клиент:</b>\n{customer_text}\n"
                f"📱 Telegram: {telegram_line}\n"
                f"🆔 ID: {telegram_id_line}\n"
                f"📞 {customer.get('phone', '—')}\n"
                f"📍 {customer.get('address', '—')}\n\n"
                f"🧩 <b>Состав:</b>\n{players_text}"
            )

            if ADMIN_CHAT_ID:
                bot.send_message(ADMIN_CHAT_ID, admin_message,
                                 parse_mode="HTML")

            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                "📩 Написать в поддержку", url="https://t.me/kylo_gg"))

            bot.send_message(
                chat_id, f"✅ <b>Спасибо за заказ!</b>\n\n📦 Номер заказа: <b>№{order_id}</b>\n\n📝 Если есть вопросы — напишите нам.", parse_mode="HTML", reply_markup=markup)

        except Exception as e:
            logger.error(f"❌ Ошибка обработки заказа: {e}")

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
    bot.send_message(message.chat.id, "Нажмите кнопку ниже 👇",
                     reply_markup=markup)


@app.route('/health', methods=['GET'])
def health():
    return "OK", 200


def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    logger.info("✅ Webhook set")


if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

import telebot
import json
import time
import logging
import sys

# Настройки
BOT_TOKEN = "8523781397:AAES_yF9SIUwUqAIQVVC99bhDDIVAIFSYKE"
YOUR_TELEGRAM_ID = 985380350

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

def safe_send_message(chat_id, text, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return bot.send_message(chat_id, text)
        except Exception as e:
            logger.error(f"Ошибка отправки (попытка {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    return None

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

    safe_send_message(YOUR_TELEGRAM_ID, text)
    bot.reply_to(message, "Спасибо! Ваш заказ принят.")

@bot.message_handler(func=lambda message: True)
def handle_other(message):
    logger.debug(f"Другое сообщение: {message.content_type}")

if __name__ == "__main__":
    logger.info("🚀 Бот запускается...")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            logger.error(f"❌ Ошибка polling: {e}")
            logger.info("Перезапуск через 5 секунд...")
            time.sleep(5)

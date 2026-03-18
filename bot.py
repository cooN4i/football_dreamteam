import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройки
BOT_TOKEN = "8523781397:AAES_yF9SIUwUqAIQVVC99bhDDIVAIFSYKE"
YOUR_TELEGRAM_ID = 985380350

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ✅ Включаем получение web_app_data (для старых версий, но оставим)
dp.message.include_media_content_types = True

# 🔍 Мидлварь для логирования всех апдейтов
@dp.update.outer_middleware()
async def log_all_updates(handler, event, data):
    print(f"📥 Получен апдейт: {event}")
    return await handler(event, data)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    print(f"Команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "Привет! Это бот для приёма заказов из мини-приложения.\n"
        "Заполни состав в приложении, нажми «Подтвердить» — данные придут сюда."
    )

@dp.message()
async def handle_web_app_data(message: types.Message):
    print(f"🔥 Получено сообщение от {message.from_user.id}")
    print(f"📦 Тип сообщения: {message.content_type}")
    print(f"🧩 Есть web_app_data: {message.web_app_data is not None}")

    if not message.web_app_data:
        print("⛔ Нет web_app_data, игнорируем")
        return

    data = message.web_app_data.data
    print(f"✅ Получены сырые данные: {data}")

    try:
        order = json.loads(data)
        print(f"📊 Распарсенный JSON: {order}")
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        await message.answer("Ошибка: не удалось разобрать данные.")
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

    print(f"📤 Отправляю заказ пользователю {YOUR_TELEGRAM_ID}")
    try:
        await bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=text, parse_mode="Markdown")
        print("✅ Сообщение администратору отправлено")
    except Exception as e:
        print(f"❌ Ошибка при отправке администратору: {e}")

    print(f"📤 Отправляю подтверждение пользователю {message.from_user.id}")
    await message.answer("Спасибо! Ваш заказ принят.")

async def main():
    print("🚀 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

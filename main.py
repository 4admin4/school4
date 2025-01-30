import logging
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Встав свій токен від BotFather
TOKEN = "7620525697:AAFmUw8Dco4lt2PhWgfA22lVH_1EuzaBtRs"

logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Створюємо клавіатуру з кнопкою "Старт"
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Старт")]
    ],
    resize_keyboard=True  # Робимо кнопку компактною
)

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Натисни кнопку \"Старт\" 👇", reply_markup=keyboard)

# Обробник натискання кнопки "Старт"
@dp.message()
async def button_handler(message: types.Message):
    if message.text == "🚀 Старт":
        await message.answer("Бот запущено! ✅")

# Головна функція для запуску бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

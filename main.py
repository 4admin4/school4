import logging
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Встав свій токен від BotFather
TOKEN = "7620525697:AAFmUw8Dco4lt2PhWgfA22lVH_1EuzaBtRs"

# Логування
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Я твій Telegram-бот. Напиши мені щось або скористайся командами /help або /random.")

# Обробник команди /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Я можу виконувати наступні команди:\n/start - почати спілкування\n/help - список команд\n/random - випадкове число")

# Обробник команди /random
@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    number = random.randint(1, 100)
    await message.answer(f"Твоє випадкове число: {number}")

# Обробник звичайних повідомлень
@dp.message()
async def echo_message(message: types.Message):
    await message.answer(f"Ти написав: {message.text}")

# Головна функція для запуску бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

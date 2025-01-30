import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

# Встав свій токен від BotFather
TOKEN = "7620525697:AAFmUw8Dco4lt2PhWgfA22lVH_1EuzaBtRs"

logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

#Кнопки
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Привіт"), KeyboardButton(text="Як справи?")],
        [KeyboardButton(text="Розклад"), KeyboardButton(text="Школа")]
    ],
    resize_keyboard=True  # Робимо кнопки компактними
)

# Список відповідей
RESPONSES = {
    "Привіт": "Привіт! Як справи? 😊",
    "Як справи?": "Все чудово! А в тебе?",
    
    "Школа": "Гімназія №4 Павлоградської міської ради.\n"
             "Поштова адреса:\n"
             "вул. Корольова Сергія, буд. 3,\n"
             "м. Павлоград, Дніпропетровська область,\n"
             "Україна. 51400 📚"
}

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Вибери питання:", reply_markup=keyboard)


#Картинка розклад
@dp.message(F.text == "Розклад")
async def send_schedule(message: types.Message):
    try:
        photo = FSInputFile("schedule.jpg")  # Загружаем файл правильно
        await bot.send_photo(message.chat.id, photo)
    except FileNotFoundError:
        await message.answer("Файл з розкладом не знайдено!")
        
# Обробник натискання кнопок
@dp.message()
async def handle_buttons(message: types.Message):
    text = message.text.strip()  # Видаляємо зайві пробіли
    response = RESPONSES.get(text, "Я не знаю, що відповісти... 😅")
    await message.answer(response)
# Головна функція для запуску бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

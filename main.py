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
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Привіт"), KeyboardButton(text="Як справи?")],
        [KeyboardButton(text="Розклад"), KeyboardButton(text="Школа")]
    ],
    resize_keyboard=True  # Робимо кнопки компактними
)


# Клавіатура після "Як справи?" підменю
status_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добре"), KeyboardButton(text="Погано")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)



# Список відповідей
RESPONSES = {
    "Привіт": "Привіт! Як справи? 😊",
    "Добре": "Радий це чути! 😊",
    "Погано": "Шкода... Все добре, я поруч. Давай глибоко вдихнемо разом... вдих... видих... Ти в безпеці, і все буде добре. Якщо хочеш, можемо обійнятися або поговорити про щось приємне. ❤️",
    
    "Школа": "Гімназія №4 Павлоградської міської ради.\n"
             "Поштова адреса:\n"
             "вул. Корольова Сергія, буд. 3,\n"
             "м. Павлоград, Дніпропетровська область,\n"
             "Україна. 51400 📚"
}

# Обробник команди /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Вибери питання:", reply_markup=main_keyboard)


#Картинка розклад
@dp.message(F.text == "Розклад")
async def send_schedule(message: types.Message):
    try:
        photo = FSInputFile("schedule.jpg")  # Загружаем файл правильно
        await bot.send_photo(message.chat.id, photo)
    except FileNotFoundError:
        await message.answer("Файл з розкладом не знайдено!")
        

# Обробник кнопки "Як справи?"
@dp.message(F.text == "Як справи?")
async def ask_status(message: types.Message):
    await message.answer("Обери варіант:", reply_markup=status_keyboard)

# Обробник кнопки "Назад"
@dp.message(F.text == "Назад")
async def go_back(message: types.Message):
    await message.answer("Повертаємося назад!", reply_markup=main_keyboard)


# Обработчик остальных сообщений
@dp.message()
async def handle_buttons(message: types.Message):
    text = message.text.strip()  # Убираем лишние пробелы
    response = RESPONSES.get(text, "Я не знаю, что ответить... 😅")
    await message.answer(response)


# Головна функція для запуску бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

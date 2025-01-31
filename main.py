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
        [KeyboardButton(text="Привіт"), KeyboardButton(text="Вікторина")],
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

# Клавіатура після "Вікторини" підменю
vik_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Старт"),KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)

# Список відповідей
RESPONSES = {
    "Вікторина": "Чудово! Тепер починається справжня інтелектуальна пригода! 🚀🧠 Готовий перевірити свої знання? Натискай та поринь у світ захопливих запитань! \n" " \n" "🧐шукай коди вводь", 
    "Добре": "Радий це чути! 😊",
    "Старт": "Почнемо з простого🥳. Обери надійний пароль з наявних та введи його.\n" "( pas123; Nastya12; !N43i@_2nisU )",
    "!N43i@_2nisU": "Молодець🤩, ти переміг забери подарунок https://viktorina.webnode.com.ua/",
    "123w": "⚠️ Не переходь на невідомі посилання та не завантажуй підозрілі файли! Це може призвести до крадіжки паролів, вірусів і зламу акаунтів. Будь обережним! 🔒\n"
    "😜Продовжимо знайди відео в ютуб ____ переглянь відшукай код",
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
@dp.message(F.text == "Привіт")
async def ask_status(message: types.Message):
    await message.answer("Привіт👋≧◉ᴥ◉≦ Як справи?", reply_markup=status_keyboard)

#Обробка кнопки Вікторина
@dp.message(F.text == "Вікторина")
async def ask_status(message: types.Message):
    await message.answer("Чудово! Тепер починається справжня інтелектуальна пригода! 🚀🧠 Готовий перевірити свої знання? Натискай та поринь у світ захопливих запитань!", reply_markup=vik_keyboard)

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

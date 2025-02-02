import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

# Встав свій токен від BotFather
TOKEN = "7620525697:AAFmUw8Dco4lt2PhWgfA22lVH_1EuzaBtRs"
ADMIN_ID = 7287864631  # Вкажи Telegram ID адміністратора
logging.basicConfig(level=logging.INFO)

# Ініціалізація бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

#Кнопки
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Привіт"), KeyboardButton(text="Вікторина")],
        [KeyboardButton(text="Розклад"), KeyboardButton(text="Школа"), KeyboardButton(text="Допомога")]
    ],
    resize_keyboard=True  # Робимо кнопки компактними
)


# Клавіатура після "Як справи?" підменю
status_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добре"), KeyboardButton(text="Погано")],
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
    "Вікторина": "Чудово! 🚀🧠 Готовий перевірити свої знання? Натискай та поринь у світ захопливих запитань!\n" "шукай паролі вводи для продовження", 
   
    "Старт": "Почнемо з простого🥳. Обери надійний пароль з наявних та введи його.\n" "( pas123; Nastya12; !N43i@_2nisU )",
    "!N43i@_2nisU": "Молодець🤩, ти переміг забери подарунок https://viktorina.webnode.com.ua/",
    "123w": "⚠️ Не переходь на невідомі посилання та не завантажуй підозрілі файли! Це може призвести до крадіжки паролів, вірусів і зламу акаунтів. Будь обережним! 🔒\n"
            "😜Продовжимо знайди відео в ютуб https://youtu.be/fV_ayiS9Xy4",
    "фішинг": "Супер🏅. Для того щоб уникнути фішингу🎣\n"
            "Перевіряй URL – не переходь за підозрілими посиланнями\n"
            "Не вводь дані на незнайомих сайтах \n"
            "Перевіряй відправника листів і повідомлень\n"
            "Не завантажуй підозрілі файли\n"
            "Будь обережний із SMS та дзвінками \n"
            "Давай перевірим чи знаєш 🔍 адресу офіційного сайту Гімназії №4",
    "Фішинг": "Супер🏅. Для того щоб уникнути фішингу🎣\n"
            "Перевіряй URL – не переходь за підозрілими посиланнями\n"
            "Не вводь дані на незнайомих сайтах \n"
            "Перевіряй відправника листів і повідомлень\n"
            "Не завантажуй підозрілі файли\n"
            "Будь обережний із SMS та дзвінками \n"
            "Давай перевірим чи знаєш 🔍 адресу офіційного сайту Гімназії №4",
    "sc4.dp.ua" : " Вітаємо з перемогою! 🎉\n"
                "Ви продемонстрували чудові знання, кмітливість і наполегливість у нашій інтернет-вікторині! Ця перемога — заслужена нагорода за вашу допитливість і прагнення до нових знань.\n"
                "Нехай цей успіх стане для вас ще одним кроком до великих досягнень! 🚀",
    "https://www.sc4.dp.ua/":" Вітаємо з перемогою! 🎉\n"
                "Ви продемонстрували чудові знання, кмітливість і наполегливість у нашій інтернет-вікторині! Ця перемога — заслужена нагорода за вашу допитливість і прагнення до нових знань.\n"
                "Нехай цей успіх стане для вас ще одним кроком до великих досягнень! 🚀",
    "Sc4.dp.ua" : " Вітаємо з перемогою! 🎉\n"
                "Ви продемонстрували чудові знання, кмітливість і наполегливість у нашій інтернет-вікторині! Ця перемога — заслужена нагорода за вашу допитливість і прагнення до нових знань.\n"
                "Нехай цей успіх стане для вас ще одним кроком до великих досягнень! 🚀",
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

#Картинка  ребус
@dp.message(F.text == "Panda" or "panda")
async def send_schedule(message: types.Message):
    try:
        photo = FSInputFile("reb.jpg")  # Загружаем файл правильно
        await message.answer("Так тримати, не зупиняйся. Розгадай ребус")
        await bot.send_photo(message.chat.id, photo)
    except FileNotFoundError:
        await message.answer("Файл не знайдено!")

# Обробник кнопки "Як справи?"
@dp.message(F.text == "Привіт")
async def ask_status(message: types.Message):
    await message.answer("Привіт👋≧◉ᴥ◉≦ Як справи?", reply_markup=status_keyboard)

# Обробник кнопки "Добре"
@dp.message(F.text == "Добре")
async def ask_status(message: types.Message):
    await message.answer("Радий це чути! 😊", reply_markup=main_keyboard)

# Обробник кнопки "Погано"
@dp.message(F.text == "Погано")
async def ask_status(message: types.Message):
    await message.answer("Шкода... Все добре, я поруч. Давай глибоко вдихнемо разом... вдих... видих... Ти в безпеці, і все буде добре. Якщо хочеш, можемо обійнятися або поговорити про щось приємне. ❤️", reply_markup=main_keyboard)

#Обробка кнопки Вікторина
@dp.message(F.text == "Вікторина")
async def ask_status(message: types.Message):
    await message.answer("Чудово! Тепер починається справжня інтелектуальна пригода! 🚀🧠 Готовий перевірити свої знання? Натискай та поринь у світ захопливих запитань!\n" "🧐Шукай коди (pass) вводь для продовження", reply_markup=vik_keyboard)

# Обробник кнопки "Назад"
@dp.message(F.text == "Назад")
async def go_back(message: types.Message):
    await message.answer("Повертаємося назад!", reply_markup=main_keyboard)



# Обробник кнопки "Допомога"
@dp.message(F.text == "Допомога")
async def send_help_request(message: types.Message):
    await message.answer("Будь ласка, опиши свою проблему, і я передам її адміністрації.")
    
    # Встановлюємо стан очікування повідомлення від користувача
    @dp.message()
    async def forward_to_admin(msg: types.Message):
        await bot.send_message(ADMIN_ID, f"📩 Запит від @{msg.from_user.username} ({msg.from_user.id}):\n\n{msg.text}")
        await msg.answer("Ваше повідомлення передано адміністрації. Очікуйте відповідь.")

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

import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# 1. Різні стани для різних дій
class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_password_reset = State()

TOKEN = "7620525697:AAFmUw8Dco4lt2PhWgfA22lVH_1EuzaBtRs"
ADMIN_ID = 7287864631
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВІАТУРИ ---
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Привіт"), KeyboardButton(text="Вікторина")],
        [KeyboardButton(text="Розклад"), KeyboardButton(text="Школа"), KeyboardButton(text="Допомога")]
    ],
    resize_keyboard=True
)

help_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Залишити пропозицію"), KeyboardButton(text="Часті запитання (FAQ)")],
        [KeyboardButton(text="Відновити пароль аккаунта")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True
)

status_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Добре"), KeyboardButton(text="Погано")]],
    resize_keyboard=True
)

vik_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Старт"), KeyboardButton(text="Назад")]],
    resize_keyboard=True
)

# --- ВІДПОВІДІ ---
RESPONSES = {
    "Старт": "Почнемо з простого🥳. Обери надійний пароль...",
    "N43i@_2nisU": "Молодець🤩, ти переміг! Подарунок: https://viktorina.webnode.com.ua/",
    "Школа": "Гімназія №4 Павлоградської міської ради.\n📍 Адреса: вул. Корольова Сергія, 3.",
    # Додайте інші ключі сюди...
}

# --- ОБРОБНИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привіт! Вибери питання:", reply_markup=main_keyboard)

@dp.message(F.text == "Розклад")
async def send_schedule(message: types.Message):
    try:
        photo = FSInputFile("schedule.jpg")
        await message.answer_photo(photo, caption="Ваш розклад")
    except Exception:
        await message.answer("Файл з розкладом не знайдено!")

@dp.message(F.text.casefold() == "panda")
async def send_rebus(message: types.Message):
    try:
        photo = FSInputFile("reb.jpg")
        await message.answer("Так тримати! Розгадай ребус:")
        await message.answer_photo(photo)
    except Exception:
        await message.answer("Файл не знайдено!")

@dp.message(F.text == "Привіт")
async def ask_status(message: types.Message):
    await message.answer("Привіт👋 Як справи?", reply_markup=status_keyboard)

@dp.message(F.text == "Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть питання:", reply_markup=help_keyboard)

# --- РОБОТА З FSM (СТАНИ) ---

@dp.message(F.text == "Залишити пропозицію")
async def suggest_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть вашу пропозицію:")
    await state.set_state(BotStates.waiting_for_suggestion)

@dp.message(BotStates.waiting_for_suggestion)
async def suggest_finish(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"📩 Пропозиція від @{message.from_user.username}:\n{message.text}")
    await message.answer("Дякуємо! Пропозицію надіслано.", reply_markup=main_keyboard)
    await state.clear()

@dp.message(F.text == "Відновити пароль аккаунта")
async def pass_start(message: types.Message, state: FSMContext):
    await message.answer("Вкажіть ПІБ, клас та акаунт:")
    await state.set_state(BotStates.waiting_for_password_reset)

@dp.message(BotStates.waiting_for_password_reset)
async def pass_finish(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"🔑 Запит на пароль від @{message.from_user.username}:\n{message.text}")
    await message.answer("Запит надіслано адміністратору.", reply_markup=main_keyboard)
    await state.clear()

# --- FAQ (Виправлено Markdown) ---
@dp.message(F.text == "Часті запитання (FAQ)")
async def faq_cmd(message: types.Message):
    text = (
        "*Google Клас не завантажує урок*\n"
        "• Переконайся, що встановлено пароль на екран телефону\n"
        "• Перевір налаштування батьківського контролю\n\n"
        "*Не працює відеоурок*\n"
        "• Найчастіше проблема у Google Family Link"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard)

# --- ЗАГАЛЬНИЙ ОБРОБНИК ---
@dp.message()
async def handle_buttons(message: types.Message):
    res = RESPONSES.get(message.text)
    if res:
        await message.answer(res)
    elif message.text == "Назад":
        await message.answer("Головне меню", reply_markup=main_keyboard)
    else:
        await message.answer("Я не впевнений, що розумію. Спробуйте скористатися кнопками.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    "N43i@_2nisU": "Молодець🤩, ти переміг! Забери подарунок: https://viktorina.webnode.com.ua/",
    "123w":"⚠️ Не переходь на невідомі посилання та не завантажуй підозрілі файли! "
    "Це може призвести до крадіжки паролів, вірусів і зламу акаунтів. Будь обережним! 🔒\n"
    "😜 Продовжимо: знайди відео в YouTube https://youtu.be/fV_ayiS9Xy4",
    "фішинг":"Супер🏅. Для того щоб уникнути фішингу🎣:\n"
        "🔹 Перевіряй URL – не переходь за підозрілими посиланнями\n"
        "🔹 Не вводь дані на незнайомих сайтах\n"
        "🔹 Перевіряй відправника листів і повідомлень\n"
        "🔹 Не завантажуй підозрілі файли\n"
        "🔹 Будь обережний із SMS та дзвінками\n\n"
        "*Давай перевіримо, чи знаєш 🔍 адресу офіційного сайту Гімназії №4.*",
    "sc4.dp.ua":"🎉 Вітаємо з перемогою!\n"
        "Ви продемонстрували чудові знання, кмітливість і наполегливість у нашій вікторині! "
        "Нехай цей успіх стане для вас ще одним кроком до великих досягнень! 🚀",
    "https://www.sc4.dp.ua/":"🎉 Вітаємо з перемогою!\n"
        "Ви продемонстрували чудові знання, кмітливість і наполегливість у нашій вікторині! "
        "Нехай цей успіх стане для вас ще одним кроком до великих досягнень! 🚀",
    "Школа":"Гімназія №4 Павлоградської міської ради.\n"
        "📍 Адреса:\n"
        "вул. Корольова Сергія, буд. 3,\n"
        "м. Павлоград, Дніпропетровська область,\n"
        "Україна, 51400 📚",
    "Фішинг":"Супер🏅. Для того щоб уникнути фішингу🎣:\n"
        "🔹 Перевіряй URL – не переходь за підозрілими посиланнями\n"
        "🔹 Не вводь дані на незнайомих сайтах\n"
        "🔹 Перевіряй відправника листів і повідомлень\n"
        "🔹 Не завантажуй підозрілі файли\n"
        "🔹 Будь обережний із SMS та дзвінками\n\n"
        "*Давай перевіримо, чи знаєш 🔍 адресу офіційного сайту Гімназії №4.*",
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


# Обробник кнопки help
@dp.message(F.text == "Допомога")
async def go_back(message: types.Message):
    await message.answer("Оберіть з якого питання вам потрібна допомога", reply_markup=help_keyboard)



# Обробник кнопки "Пропозиція"1
@dp.message(F.text == "Залишити пропозицію")
async def send_help_request(message: types.Message, state: FSMContext):
    await message.answer("Залиште свою пропозицію, і ми обов’язково її розглянемо! Ваші ідеї важливі для нас. 😊")
    await state.set_state(HelpRequest.waiting_for_message)  # Встановлюємо стан

# О2
@dp.message(HelpRequest.waiting_for_message)
async def forward_to_admin(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"📩 Пропозиція від @{message.from_user.username} :\n\n{message.text}")
    await message.answer("Ваше повідомлення передано адміністрації. Очікуйте відповідь.",reply_markup=main_keyboard)
    await state.clear()  # Завершуємо стан


# Обробник кнопки "Часті питання"1
@dp.message(F.text == "Часті запитання (FAQ)")
async def ask_status(message: types.Message):
    await message.answer(
        "*Ввів аккаунт та пароль, але Google Клас не завантажує урок*\n"
        "Переконайся, чи є пароль на телефоні\n"
        "Інколи батьківський контроль блокує роботу\n\n"
        "*Не працює долучення до відеоуроку*\n"
        "Проблема в батьківському контролі\n",
        parse_mode="MarkdownV2",
        reply_markup=main_keyboard
    )


# Обробник кнопки "Відновити пароль аккаута
@dp.message(F.text == "Відновити пароль аккаунта")
async def send_help_request(message: types.Message, state: FSMContext):
    await message.answer("Будь ласка, вкажіть свій акаунт або Прізвище, Ім'я, клас, а також, що потрібно відновити.")
    await state.set_state(HelpRequest.waiting_for_message)  # Встановлюємо стан

# Обробник повідомлення після "Допомога"
@dp.message(HelpRequest.waiting_for_message)
async def forward_to_admin(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"📩 Відновлення пароля від @{message.from_user.username}:\n\n{message.text}")
    await message.answer("Ваше повідомлення передано адміністрації. Очікуйте відповідь.",reply_markup=main_keyboard)
    await state.clear()  # Завершуємо стан

#________________
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

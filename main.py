import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# 1. СТАНИ (FSM)
class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_password_reset = State()

# БЕРЕМО ТОКЕН З ENVIRONMENT (налаштували в Render)
TOKEN = os.getenv("BOT_TOKEN", "8602310062:AAEHbEKlma1p7oT9yuJFISuqbnolgk-0l9I")
ADMIN_ID = 8635308149

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

# --- СЛОВНИК ВІДПОВІДЕЙ ---
RESPONSES = {
    "Старт": "Почнемо з простого🥳. Обери надійний пароль...",
    "N43i@_2nisU": "Молодець🤩, ти переміг! Забери подарунок: https://viktorina.webnode.com.ua/",
    "123w": "⚠️ Не переходь на невідомі посилання! Це може призвести до зламу. Продовжимо: https://youtu.be/fV_ayiS9Xy4",
    "фішинг": "Супер🏅. Перевіряй URL та не вводь дані на незнайомих сайтах. Знаєш адресу сайту Гімназії №4?",
    "sc4.dp.ua": "🎉 Вітаємо з перемогою! Ви продемонстрували чудові знання!",
    "Школа": "Гімназія №4 Павлоградської міської ради.\n📍 вул. Корольова Сергія, 3."
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

@dp.message(F.text.in_({"Panda", "panda"}))
async def send_rebus(message: types.Message):
    try:
        photo = FSInputFile("reb.jpg")
        await message.answer("Так тримати! Розгадай ребус:")
        await message.answer_photo(photo)
    except Exception:
        await message.answer("Файл ребуса не знайдено!")

@dp.message(F.text == "Привіт")
async def hello_msg(message: types.Message):
    await message.answer("Привіт👋 Як справи?", reply_markup=status_keyboard)

@dp.message(F.text == "Добре")
async def status_ok(message: types.Message):
    await message.answer("Радий це чути! 😊", reply_markup=main_keyboard)

@dp.message(F.text == "Погано")
async def status_bad(message: types.Message):
    await message.answer("Шкода... Все буде добре, я поруч. ❤️", reply_markup=main_keyboard)

@dp.message(F.text == "Вікторина")
async def start_quiz(message: types.Message):
    await message.answer("Чудово! Починаємо вікторину! Шукай коди для продовження.", reply_markup=vik_keyboard)

@dp.message(F.text == "Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть питання:", reply_markup=help_keyboard)

@dp.message(F.text == "Назад")
async def go_back(message: types.Message):
    await message.answer("Головне меню", reply_markup=main_keyboard)

# --- FSM ОБРОБНИКИ ---

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
async def pass_reset_start(message: types.Message, state: FSMContext):
    await message.answer("Вкажіть ПІБ, клас та акаунт:")
    await state.set_state(BotStates.waiting_for_password_reset)

@dp.message(BotStates.waiting_for_password_reset)
async def pass_reset_finish(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"🔑 Запит на пароль від @{message.from_user.username}:\n{message.text}")
    await message.answer("Запит надіслано адміністратору.", reply_markup=main_keyboard)
    await state.clear()

@dp.message(F.text == "Часті запитання (FAQ)")
async def faq_cmd(message: types.Message):
    text = (
        "**Google Клас не завантажує урок**\n"
        "• Переконайся, що встановлено пароль на екран\n"
        "• Перевір Family Link\n"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard)

# --- ЗАГАЛЬНИЙ ОБРОБНИК ---
@dp.message()
async def handle_all(message: types.Message):
    res = RESPONSES.get(message.text)
    if res:
        await message.answer(res)
    else:
        await message.answer("Я не впевнений, що розумію. Використовуйте кнопки або введіть код.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

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

# НАЛАШТУВАННЯ (Токен та ID адміна)
TOKEN = os.getenv("BOT_TOKEN", "8602310062:AAEHbEKlma1p7oT9yuJFISuqbnolgk-0l9I")
ADMIN_ID = 8635308149

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВІАТУРИ ---
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Розклад 🔔"), KeyboardButton(text="❓ Допомога")],
        [KeyboardButton(text="🎮 Вікторина"), KeyboardButton(text="🏫 Школа")]
    ],
    resize_keyboard=True
)

help_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💡 Залишити пропозицію"), KeyboardButton(text="📝 FAQ")],
        [KeyboardButton(text="🔑 Відновити пароль")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

vik_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🚀 Старт Вікторини"), KeyboardButton(text="⬅️ Назад")]],
    resize_keyboard=True
)

# --- СЛОВНИК ВІДПОВІДЕЙ (Коди для вікторини) ---
RESPONSES = {
    "N43i@_2nisU": "Молодець🤩, ти переміг! Тримай секретний бонус.",
    "123w": "⚠️ Не переходь на невідомі посилання! Продовжуємо: https://youtu.be/fV_ayiS9Xy4",
    "фішинг": "Супер🏅. Знаєш адресу офіційного сайту Гімназії №4?"
}

# --- ОБРОБНИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Вітаємо у боті Гімназії №4! Оберіть потрібний розділ:", reply_markup=main_keyboard)

# РОЗДІЛ: РОЗКЛАД
@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    try:
        photo = FSInputFile("schedule.jpg")
        await message.answer_photo(photo, caption="📅 Поточний розклад занять")
    except Exception:
        await message.answer("❌ Файл з розкладом тимчасово відсутній на сервері.")

# РОЗДІЛ: ШКОЛА
@dp.message(F.text == "🏫 Школа")
async def school_info(message: types.Message):
    text = (
        "<b>Гімназія №4 Павлоградської міської ради</b>\n\n"
        "📍 <b>Адреса:</b> вул. Корольова Сергія, 3\n"
        "🔗 <a href='https://sc4.dp.ua/'>Офіційний сайт</a>\n"
        "🗺 <a href='https://www.google.com/maps/search/?api=1&query=вулиця+Корольова+Сергія+3+Павлоград'>Ми на карті</a>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=False)

# РОЗДІЛ: ВІКТОРИНА (Окремий блок для редагування)
@dp.message(F.text == "🎮 Вікторина")
async def quiz_menu(message: types.Message):
    await message.answer(
        "Ласкаво просимо до інтелектуальної гри! 🧠\n"
        "Тут ви можете перевірити свої знання. Натисніть 'Старт', щоб почати.",
        reply_markup=vik_keyboard
    )

@dp.message(F.text == "🚀 Старт Вікторини")
async def start_quiz_logic(message: types.Message):
    # Тут можна міняти перше питання вікторини
    await message.answer("Питання №1: Який пароль найбезпечніший? (Введіть відповідь кодом)")

# РОЗДІЛ: ДОПОМОГА
@dp.message(F.text == "❓ Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть тип допомоги:", reply_markup=help_keyboard)

@dp.message(F.text == "⬅️ Назад")
async def go_back(message: types.Message):
    await message.answer("Повертаємось у головне меню", reply_markup=main_keyboard)

# --- РОБОТА З ФОРМАМИ (FSM) ---

@dp.message(F.text == "💡 Залишити пропозицію")
async def suggest_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть вашу ідею або пропозицію одним повідомленням:")
    await state.set_state(BotStates.waiting_for_suggestion)

@dp.message(F.text == "🔑 Відновити пароль")
async def pass_reset_start(message: types.Message, state: FSMContext):
    await message.answer("Вкажіть ПІБ, клас та назву акаунта (якщо пам'ятаєте):")
    await state.set_state(BotStates.waiting_for_password_reset)

# Обробник отримання даних (універсальний)
@dp.message(BotStates.waiting_for_suggestion)
@dp.message(BotStates.waiting_for_password_reset)
async def process_fsm_data(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    prefix = "📩 ПРОПОЗИЦІЯ" if current_state == BotStates.waiting_for_suggestion else "🔑 ПАРОЛЬ"
    
    await bot.send_message(
        ADMIN_ID, 
        f"<b>{prefix}</b>\nВід: @{message.from_user.username}\nТекст: {message.text}",
        parse_mode="HTML"
    )
    await message.answer("✅ Ваше повідомлення надіслано адміністрації!", reply_markup=main_keyboard)
    await state.clear()

@dp.message(F.text == "📝 FAQ")
async def faq_cmd(message: types.Message):
    text = (
        "<b>Часті запитання (FAQ)</b>\n\n"
        "❓ <b>Не заходить у Google Classroom?</b>\n"
        "Перевірте, чи встановлено PIN-код на екрані телефону.\n\n"
        "❓ <b>Де знайти розклад?</b>\n"
        "Натисніть кнопку 'Розклад' у головному меню."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_keyboard)

# ЗАГАЛЬНИЙ ОБРОБНИК (КОДИ)
@dp.message()
async def handle_all(message: types.Message):
    res = RESPONSES.get(message.text)
    if res:
        await message.answer(res)
    else:
        await message.answer("Вибачте, я не зрозумів. Скористайтеся меню або введіть правильний код вікторини.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

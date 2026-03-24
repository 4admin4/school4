import logging
import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiohttp import web

# --- 1. НАЛАШТУВАННЯ ---
TOKEN = os.getenv("BOT_TOKEN", "8602310062:AAEHbEKlma1p7oT9yuJFISuqbnolgk-0l9I")
ADMIN_ID = 8635308149 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 2. БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    conn.commit()
    conn.close()

def save_schedule_id(photo_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("schedule_id", photo_id))
    conn.commit()
    conn.close()

def get_schedule_id():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", ("schedule_id",))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

init_db()

# --- 3. СТАНИ ---
class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_password_reset = State()
    quiz_q1 = State()
    quiz_q2 = State()
    quiz_q3 = State()

# --- 4. КЛАВІАТУРИ ---
def get_quiz_kb():
    keyboard = [
        [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
        [KeyboardButton(text="⬅️ Назад")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

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

# --- 5. ВЕБ-СЕРВЕР (ФІКС ОБРИВУ) ---
async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

# --- 6. ОБРОБНИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    await message.answer("Вітаємо у боті Гімназії №4!", reply_markup=main_keyboard)

@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def update_schedule(message: types.Message):
    save_schedule_id(message.photo[-1].file_id)
    await message.answer("✅ Розклад оновлено!")

@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    photo_id = get_schedule_id()
    if photo_id:
        await message.answer_photo(photo=photo_id, caption="📅 Актуальний розклад")
    else:
        await message.answer("❌ Розклад ще не завантажено.")

# Вікторина
@dp.message(F.text == "🎮 Вікторина")
async def quiz_menu(message: types.Message):
    await message.answer("Готові до гри?", reply_markup=vik_keyboard)

@dp.message(F.text == "🚀 Старт Вікторини")
async def start_quiz(message: types.Message, state: FSMContext):
    await message.answer("Питання 1: Тобі прийшло SMS про виграш. Що зробиш?\n1. Перейду\n2. Видалю\n3. Перешлю", reply_markup=get_quiz_kb())
    await state.set_state(BotStates.quiz_q1)

@dp.message(BotStates.quiz_q1)
async def q1(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад": return await cmd_start(message, state)
    if message.text == "2":
        await message.answer("✅ Вірно! Питання 2: Який пароль кращий?\n1. 1234\n2. qwerty\n3. Tr0n_&_4", reply_markup=get_quiz_kb())
        await state.set_state(BotStates.quiz_q2)
    else: await message.answer("❌ Помилка. Обери 2.")

@dp.message(BotStates.quiz_q2)
async def q2(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад": return await cmd_start(message, state)
    if message.text == "3":
        await message.answer("✅ Супер! Питання 3: Можна давати пароль друзям?\n1. Так\n2. Можливо\n3. Ніколи", reply_markup=get_quiz_kb())
        await state.set_state(BotStates.quiz_q3)
    else: await message.answer("❌ Обери 3.")

@dp.message(BotStates.quiz_q3)
async def q3(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад": return await cmd_start(message, state)
    if message.text == "3":
        await message.answer("🏆 Перемога!", reply_markup=main_keyboard)
        await state.clear()
    else: await message.answer("❌ Обери 3.")

@dp.message(F.text == "⬅️ Назад")
async def back_button(message: types.Message, state: FSMContext):
    await cmd_start(message, state)

@dp.message(F.text == "🏫 Школа")
async def school_info(message: types.Message):
    text = (
        "<b>🏫 Гімназія №4 Павлоградської міської ради</b>\n\n"
        "📍 <b>Адреса:</b> <a href='https://www.google.com/maps/search/?api=1&query=вулиця+Сергія+Корольова,+3,+Павлоград'>вул. Сергія Корольова, 3</a>\n\n"
        "🔗 <b>Корисні посилання:</b>\n"
        "🔹 <a href='https://www.sc4.dp.ua/'>Офіційний сайт гімназії</a>\n"
        "🔹 <a href='https://nz.ua/'>Платформа щоденник (Надають учням та їхнім батькам постійний доступ до всієї історії отриманих оцінок)</a>\n\n"
        "🔹 <a href='https://www.facebook.com/groups/625419974786074/'>Сторінка на facebook</a>\n\n"
        "<i>Натисніть на адресу, щоб відкрити карту</i> 🗺️"
    )
    
    await message.answer(
        text, 
        parse_mode="HTML", 
        disable_web_page_preview=False  # Дозволяє показати мініатюру карти/сайту
    )

@dp.message(F.text == "❓ Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть розділ:", reply_markup=help_keyboard)

async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

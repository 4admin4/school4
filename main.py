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

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
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

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080)) 
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

# --- НАЛАШТУВАННЯ БОТА ---
TOKEN = os.getenv("BOT_TOKEN", "8602310062:AAEHbEKlma1p7oT9yuJFISuqbnolgk-0l9I")
ADMIN_ID = 8635308149

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_password_reset = State()

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

RESPONSES = {
    "N43i@_2nisU": "Молодець🤩, ти переміг!",
    "123w": "⚠️ Не переходь на невідомі посилання! https://youtu.be/fV_ayiS9Xy4",
    "фішинг": "Супер🏅. Знаєш адресу офіційного сайту Гімназії №4?"
}

# --- ОБРОБНИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Вітаємо у боті Гімназії №4!", reply_markup=main_keyboard)

# АДМІН-ОНОВЛЕННЯ РОЗКЛАДУ (Збереження в базу)
@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def update_schedule_photo(message: types.Message):
    photo_id = message.photo[-1].file_id
    save_schedule_id(photo_id)  # Зберігаємо в SQLite
    
    await message.answer(
        f"✅ <b>Розклад збережено в базу даних!</b>\n\n"
        f"Тепер учні бачитимуть це фото.\n"
        f"ID: <code>{photo_id}</code>", 
        parse_mode="HTML"
    )

@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    # Пріоритет: 1. База даних -> 2. ENV -> 3. Файл
    photo_id = get_schedule_id() or os.getenv("SCHEDULE_ID")
    
    try:
        if photo_id:
            await message.answer_photo(photo=photo_id, caption="📅 Актуальний розклад")
        else:
            photo = FSInputFile("schedule.jpg")
            await message.answer_photo(photo=photo, caption="📅 Розклад (з файлу)")
    except Exception as e:
        await message.answer("❌ Фото не налаштовано. Адмін, надішли картинку розкладу!")

@dp.message(F.text == "🏫 Школа")
async def school_info(message: types.Message):
    text = (
        "<b>Гімназія №4 Павлоградської міської ради</b>\n\n"
        "📍 <b>Адреса:</b> вул. Корольова Сергія, 3\n"
        "🔗 <a href='https://sc4.dp.ua/'>Офіційний сайт</a>"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "🎮 Вікторина")
async def quiz_menu(message: types.Message):
    await message.answer("Ласкаво просимо до гри! 🧠", reply_markup=vik_keyboard)

@dp.message(F.text == "🚀 Старт Вікторини")
async def start_quiz_logic(message: types.Message):
    await message.answer("Питання №1: Який пароль найбезпечніший?")

@dp.message(F.text == "❓ Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть тип допомоги:", reply_markup=help_keyboard)

@dp.message(F.text == "⬅️ Назад")
async def go_back(message: types.Message):
    await message.answer("Головне меню", reply_markup=main_keyboard)

@dp.message(F.text == "💡 Залишити пропозицію")
async def suggest_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть вашу пропозицію:")
    await state.set_state(BotStates.waiting_for_suggestion)

@dp.message(F.text == "🔑 Відновити пароль")
async def pass_reset_start(message: types.Message, state: FSMContext):
    await message.answer("Вкажіть ПІБ та клас:")
    await state.set_state(BotStates.waiting_for_password_reset)

@dp.message(BotStates.waiting_for_suggestion)
@dp.message(BotStates.waiting_for_password_reset)
async def process_fsm_data(message: types.Message, state: FSMContext):
    st = await state.get_state()
    pfx = "📩 ПРОПОЗИЦІЯ" if st == BotStates.waiting_for_suggestion else "🔑 ПАРОЛЬ"
    await bot.send_message(ADMIN_ID, f"<b>{pfx}</b>\nВід: @{message.from_user.username}\n{message.text}", parse_mode="HTML")
    await message.answer("✅ Надіслано!", reply_markup=main_keyboard)
    await state.clear()

@dp.message(F.text == "📝 FAQ")
async def faq_cmd(message: types.Message):
    await message.answer("<b>FAQ</b>\n\nТут ваші відповіді на питання...", parse_mode="HTML")

@dp.message()
async def handle_all(message: types.Message):
    res = RESPONSES.get(message.text)
    if res:
        await message.answer(res)
    else:
        await message.answer("Скористайтеся меню.")

async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

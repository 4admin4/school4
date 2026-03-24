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

# --- БАЗА ДАНИХ (SQLite) ---
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

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (Щоб не вимикався) ---
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

# --- СТАНИ (FSM) ---
class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_password_reset = State()
    # Стани вікторини
    quiz_q1 = State()
    quiz_q2 = State()
    quiz_q3 = State()

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

# --- ОБРОБНИКИ (Handlers) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Вітаємо у боті Гімназії №4!", reply_markup=main_keyboard)

# ОНОВЛЕННЯ РОЗКЛАДУ (Тільки для адміна)
@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def update_schedule_photo(message: types.Message):
    photo_id = message.photo[-1].file_id
    save_schedule_id(photo_id)
    await message.answer(f"✅ Розклад оновлено в базі!\nID: <code>{photo_id}</code>", parse_mode="HTML")

@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    photo_id = get_schedule_id() or os.getenv("SCHEDULE_ID")
    try:
        if photo_id:
            await message.answer_photo(photo=photo_id, caption="📅 Актуальний розклад")
        else:
            await message.answer("❌ Розклад ще не завантажено адміном.")
    except Exception:
        await message.answer("❌ Помилка при надсиланні фото.")

# --- ЛОГІКА ВІКТОРИНИ ---

@dp.message(F.text == "🎮 Вікторина")
async def quiz_menu(message: types.Message):
    await message.answer("Готові перевірити знання з безпеки?", reply_markup=vik_keyboard)

@dp.message(F.text == "🚀 Старт Вікторини")
async def start_quiz(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>Питання №1:</b> Тобі прийшло SMS: 'Ви виграли iPhone! Перейдіть за посиланням'. Що зробиш?\n\n"
        "1. Перейду і заповню дані.\n"
        "2. Видалю повідомлення, це шахраї.\n"
        "3. Надішлю друзям.", parse_mode="HTML"
    )
    await state.set_state(BotStates.quiz_q1)

@dp.message(BotStates.quiz_q1)
async def check_q1(message: types.Message, state: FSMContext):
    if "2" in message.text:
        await message.answer("✅ Правильно! Це типовий фішинг.")
        await message.answer("<b>Питання №2:</b> Який пароль найнадійніший?\n\n1. 123456\n2. qwerty\n3. Tr0n_&_Gimn4ziya", parse_mode="HTML")
        await state.set_state(BotStates.quiz_q2)
    else:
        await message.answer("❌ Це небезпечно! Обери варіант 2.")

@dp.message(BotStates.quiz_q2)
async def check_q2(message: types.Message, state: FSMContext):
    if "3" in message.text:
        await message.answer("✅ Супер! Складний пароль — твій захист.")
        await message.answer("<b>Питання №3:</b> Чи можна давати свій пароль друзям?\n\n1. Так, вони ж друзі.\n2. Тільки якщо дуже просять.\n3. Нікому і ніколи.", parse_mode="HTML")
        await state.set_state(BotStates.quiz_q3)
    else:
        await message.answer("❌ Занадто просто. Обери варіант 3.")

@dp.message(BotStates.quiz_q3)
async def check_q3(message: types.Message, state: FSMContext):
    if "3" in message.text:
        await message.answer("🏆 Вітаємо! Ти пройшов вікторину!", reply_markup=main_keyboard)
        await state.clear()
    else:
        await message.answer("❌ Пароль має бути тільки твоїм! Обери 3.")

# --- ІНШІ РОЗДІЛИ ---

@dp.message(F.text == "🏫 Школа")
async def school_info(message: types.Message):
    text = "<b>Гімназія №4 Павлоград</b>\n📍 вул. Корольова Сергія, 3\n🔗 <a href='https://sc4.dp.ua/'>Сайт</a>"
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(F.text == "❓ Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть розділ:", reply_markup=help_keyboard)

@dp.message(F.text == "⬅️ Назад")
async def go_back(message: types.Message):
    await message.answer("Головне меню", reply_markup=main_keyboard)

# --- FSM (Зворотний зв'язок) ---

@dp.message(F.text == "💡 Залишити пропозицію")
async def suggest_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть вашу пропозицію:")
    await state.set_state(BotStates.waiting_for_suggestion)

@dp.message(BotStates.waiting_for_suggestion)
async def process_suggestion(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"📩 ПРОПОЗИЦІЯ від @{message.from_user.username}:\n{message.text}")
    await message.answer("✅ Дякуємо! Надіслано адміну.", reply_markup=main_keyboard)
    await state.clear()

@dp.message()
async def handle_all(message: types.Message):
    await message.answer("Будь ласка, використовуйте кнопки меню.")

# --- ЗАПУСК ---
async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

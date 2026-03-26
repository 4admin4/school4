import logging
import asyncio
import os
import sqlite3
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiohttp import web

# --- 1. НАЛАШТУВАННЯ ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8635308149 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 2. БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_user(user_id):
    with sqlite3.connect("bot_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

def get_all_users():
    with sqlite3.connect("bot_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        return [row[0] for row in cursor.fetchall()]

def save_setting(key, value):
    with sqlite3.connect("bot_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

def get_setting(key):
    with sqlite3.connect("bot_data.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result[0] if result else None

init_db()

# --- 3. СТАНИ (FSM) ---
class BotStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_schedule_photo = State()
    waiting_for_menu_photo = State() # ДОДАНО: стан для завантаження меню

# --- 4. КЛАВІАТУРИ ---
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Розклад 🔔"), KeyboardButton(text="🎓 Центр учня")],
        [KeyboardButton(text="🏫 Про школу"), KeyboardButton(text="❓ Допомога")]
    ],
    resize_keyboard=True
)

student_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔮 Передбачення оцінки"), KeyboardButton(text="🍎 Меню їдальні")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

help_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 FAQ"), KeyboardButton(text="🔑 Відновити пароль")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

# --- 5. ВЕБ-СЕРВЕР ---
async def handle(request):
    return web.Response(text="Bot is active!", status=200)

async def run_webserver():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- 6. ОБРОБНИКИ АДМІНІСТРАТОРА ---

@dp.message(Command("set_schedule"), F.from_user.id == ADMIN_ID)
async def set_schedule_start(message: types.Message, state: FSMContext):
    await message.answer("📸 Відправте фото НОВОГО РОЗКЛАДУ:")
    await state.set_state(BotStates.waiting_for_schedule_photo)

@dp.message(BotStates.waiting_for_schedule_photo, F.photo)
async def process_schedule_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    save_setting("schedule_id", photo_id)
    await message.answer("✅ Розклад успішно оновлено!")
    await state.clear()

# ДОДАНО: обробник команди для завантаження меню (згідно з вашою нотаткою)
@dp.message(Command("set_menu"), F.from_user.id == ADMIN_ID)
async def set_menu_start(message: types.Message, state: FSMContext):
    await message.answer("📸 Відправте фото НОВОГО МЕНЮ:")
    await state.set_state(BotStates.waiting_for_menu_photo)

@dp.message(BotStates.waiting_for_menu_photo, F.photo)
async def process_menu_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    save_setting("menu_id", photo_id)
    await message.answer("✅ Меню їдальні успішно оновлено!")
    await state.clear()

@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть текст оголошення для всіх учнів:")
    await state.set_state(BotStates.waiting_for_broadcast)

@dp.message(BotStates.waiting_for_broadcast)
async def broadcast_send(message: types.Message, state: FSMContext):
    users = get_all_users()
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, f"📢 **ОГОЛОШЕННЯ:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except Exception:
            continue
    await message.answer(f"✅ Розсилка завершена для {count} учнів.")
    await state.clear()

# --- 7. ОСНОВНІ ОБРОБНИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() 
    add_user(message.from_user.id)
    await message.answer(f"Привіт, {message.from_user.first_name}! Вітаємо у боті Гімназії №4 🏫", reply_markup=main_keyboard)

@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    photo_id = get_setting("schedule_id")
    if photo_id:
        await message.answer_photo(photo=photo_id, caption="📅 Актуальний розклад")
    else:
        await message.answer("❌ Розклад ще не завантажений адміністратором.")

@dp.message(F.text == "🎓 Центр учня")
async def student_center(message: types.Message):
    await message.answer("🎓 Учнівський хаб:", reply_markup=student_keyboard)

# ДОДАНО: Логіка передбачення оцінки (згідно з вашою нотаткою)
@dp.message(F.text == "🔮 Передбачення оцінки")
async def predict_grade(message: types.Message):
    grade = random.randint(1, 12)
    predictions = [
        f"🔮 Твоє сьогоднішнє число успіху: {grade}!",
        f"📚 Зірки кажуть, сьогодні в журналі з'явиться: {grade}!",
        f"✨ Твоє передбачення на сьогодні: оцінка {grade}."
    ]
    await message.answer(random.choice(predictions))

@dp.message(F.text == "🍎 Меню їдальні")
async def school_menu(message: types.Message):
    photo_id = get_setting("menu_id")
    if photo_id:
        await message.answer_photo(photo=photo_id, caption="🍴 Сьогодні в меню")
    else:
        await message.answer("🍴 Меню ще не завантажене.")

@dp.message(F.text == "🏫 Про школу")
async def school_info(message: types.Message):
    text = (
        "<b>🏫 Гімназія №4 Павлоградської міської ради</b>\n\n"
        "📍 <b>Адреса:</b> вул. Корольова Сергія, 3\n"
        "📞 <b>Телефон:</b> (+38) 0500161966\n"
        "🔗 <a href='https://www.sc4.dp.ua/'>Офіційний сайт</a>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(F.text == "❓ Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть розділ допомоги:", reply_markup=help_keyboard)

@dp.message(F.text == "📝 FAQ")
async def faq_info(message: types.Message):
    faq_text = (
        "<b>📌 FAQ:</b>\n"
        "⏰ Дзвінки: 1-й урок з 08:00\n"
        "🛡 Безпека: під час тривоги йдемо в укриття."
    )
    await message.answer(faq_text, parse_mode="HTML")

# ДОДАНО: Відновлення пароля (текст із фото)
@dp.message(F.text == "🔑 Відновити пароль")
async def recover_password(message: types.Message):
    info_text = (
        "🔑 **Відновлення пароля:**\n\n"
        "Для відновлення доступу необхідно звернутися до свого **класного керівника** "
        "або підійти в **кабінет №27**."
    )
    await message.answer(info_text, parse_mode="Markdown")

@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear() 
    await message.answer("Повернення в головне меню", reply_markup=main_keyboard)
        
# --- 8. ЗАПУСК ---
async def main():
    await asyncio.gather(
        run_webserver(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")

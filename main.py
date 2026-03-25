import logging
import asyncio
import os
import sqlite3
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- 1. НАЛАШТУВАННЯ ТА ЛОГУВАННЯ ---
# Отримуємо токен з перемінних середовища Render
TOKEN = os.getenv("BOT_TOKEN")
# Переконайтеся, що тут лише цифри без пробілів
ADMIN_ID = 8635308149 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 2. РОБОТА З БАЗОЮ ДАНИХ (SQLite) ---
# УВАГА: На Render файл .db видаляється після кожного перезапуску!
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def save_setting(key, value):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_setting(key):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

init_db()

# --- 3. СТАНИ (FSM) ДЛЯ ДІАЛОГІВ ---
class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_broadcast = State()
    waiting_for_schedule_photo = State()
    waiting_for_menu_photo = State()

# --- 4. КЛАВІАТУРИ (Reply та Inline) ---
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Розклад 🔔"), KeyboardButton(text="🎓 Центр учня")],
        [KeyboardButton(text="🎮 Вікторина"), KeyboardButton(text="🏫 Про школу")],
        [KeyboardButton(text="❓ Допомога")]
    ],
    resize_keyboard=True
)

student_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔮 Передбачення оцінки"), KeyboardButton(text="🍎 Меню їдальні")],
        [KeyboardButton(text="💡 Залишити пропозицію"), KeyboardButton(text="⬅️ Назад")]
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

def get_quiz_kb(step):
    builder = InlineKeyboardBuilder()
    if step == 1:
        builder.row(InlineKeyboardButton(text="1. Перейду", callback_data="quiz_wrong"))
        builder.row(InlineKeyboardButton(text="2. Видалю", callback_data="quiz_step2"))
        builder.row(InlineKeyboardButton(text="3. Перешлю", callback_data="quiz_wrong"))
    elif step == 2:
        builder.row(InlineKeyboardButton(text="1. 1234", callback_data="quiz_wrong"))
        builder.row(InlineKeyboardButton(text="2. qwerty", callback_data="quiz_wrong"))
        builder.row(InlineKeyboardButton(text="3. Tr0n_&_4", callback_data="quiz_step3"))
    return builder.as_markup()

# --- 5. ВЕБ-СЕРВЕР ДЛЯ ПІНГИНГУ (Render) ---
# Цей блок відповідає на запити cron-job.org, щоб бот не засинав
async def handle(request):
    return web.Response(text="Bot is alive!", status=200)

# --- 6. АДМІНІСТРАТИВНІ ОБРОБНИКИ ---
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

@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть текст оголошення для всіх користувачів:")
    await state.set_state(BotStates.waiting_for_broadcast)

@dp.message(BotStates.waiting_for_broadcast)
async def broadcast_send(message: types.Message, state: FSMContext):
    users = get_all_users()
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, f"📢 **ВАЖЛИВЕ ПОВІДОМЛЕННЯ:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except: continue
    await message.answer(f"✅ Розсилка завершена. Отримали: {count} осіб.")
    await state.clear()

# --- 7. ЗАГАЛЬНІ ОБРОБНИКИ ТЕКСТУ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    add_user(message.from_user.id)
    await message.answer(f"Привіт, {message.from_user.first_name}! Вітаємо у боті Гімназії №4 🏫", reply_markup=main_keyboard)

@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    photo_id = get_setting("schedule_id")
    if photo_id:
        await message.answer_photo(photo=photo_id, caption="📅 Актуальний розклад занять")
    else:
        await message.answer("❌ Розклад ще не завантажений адміністратором.")

@dp.message(F.text == "🎓 Центр учня")
async def student_center(message: types.Message):
    await message.answer("🎓 Ласкаво просимо до учнівського хабу!", reply_markup=student_keyboard)

@dp.message(F.text == "🔮 Передбачення оцінки")
async def get_prediction(message: types.Message):
    res = random.choice([10, 11, 12, 9, 8, 7, "12 з зірочкою!", "Відпочинок!"])
    await message.answer(f"🔮 Магічна куля пророкує тобі сьогодні: **{res}**", parse_mode="Markdown")

@dp.message(F.text == "💡 Залишити пропозицію")
async def suggestion_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть вашу ідею анонімно:")
    await state.set_state(BotStates.waiting_for_suggestion)

@dp.message(BotStates.waiting_for_suggestion)
async def suggestion_process(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"📩 **Нова пропозиція:**\n{message.text}")
    await message.answer("✅ Дякуємо! Твою пропозицію передано.", reply_markup=student_keyboard)
    await state.clear()

@dp.message(F.text == "🏫 Про школу")
async def school_info(message: types.Message):
    text = "<b>🏫 Гімназія №4</b>\n\n📍 вул. Корольова Сергія, 3\n📞 (+38) 0500161966"
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Головне меню", reply_markup=main_keyboard)

# --- 8. ВІКТОРІНА (Inline кнопки) ---
@dp.message(F.text == "🎮 Вікторина")
async def quiz_start(message: types.Message):
    await message.answer("Питання 1: Прийшло SMS про виграш. Що зробиш?", reply_markup=get_quiz_kb(1))

@dp.callback_query(F.data == "quiz_wrong")
async def quiz_wrong(callback: types.CallbackQuery):
    await callback.answer("❌ Неправильно!", show_alert=True)

@dp.callback_query(F.data == "quiz_step2")
async def quiz_step2(callback: types.CallbackQuery):
    await callback.message.edit_text("✅ Вірно! Питання 2: Який пароль надійніший?", reply_markup=get_quiz_kb(2))

@dp.callback_query(F.data == "quiz_step3")
async def quiz_finish(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("🏆 Перемога!", reply_markup=main_keyboard)

# --- 9. ЗАПУСК ПРОЕКТУ ---
async def main():
    # Налаштування веб-сервера aiohttp
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logging.info(f"Сервер запущено на порту {port}")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск сервера та бота паралельно
    await asyncio.gather(
        site.start(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинений")

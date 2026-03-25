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

# --- 1. НАЛАШТУВАННЯ ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8635308149 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 2. БАЗА ДАНИХ (SQLite) ---
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

# --- 3. СТАНИ (FSM) ---
class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_broadcast = State()
    waiting_for_schedule_photo = State()
    waiting_for_menu_photo = State()

# --- 4. КЛАВІАТУРИ ---
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Розклад 🔔"), KeyboardButton(text="🎓 Центр учня")],
        [KeyboardButton(text="🏫 Про школу"), KeyboardButton(text="🎮 Вікторина")],
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

# --- 5. ВЕБ-СЕРВЕР (Для Render) ---
async def handle(request):
    return web.Response(text="Bot is alive!", status=200)

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

@dp.message(Command("set_menu"), F.from_user.id == ADMIN_ID)
async def set_menu_start(message: types.Message, state: FSMContext):
    await message.answer("📸 Відправте фото МЕНЮ ЇДАЛЬНІ:")
    await state.set_state(BotStates.waiting_for_menu_photo)

@dp.message(BotStates.waiting_for_menu_photo, F.photo)
async def process_menu_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    save_setting("menu_id", photo_id)
    await message.answer("✅ Меню оновлено!")
    await state.clear()

@dp.message(Command("broadcast"), F.from_user.id == ADMIN_ID)
async def broadcast_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть текст оголошення:")
    await state.set_state(BotStates.waiting_for_broadcast)

@dp.message(BotStates.waiting_for_broadcast)
async def broadcast_send(message: types.Message, state: FSMContext):
    users = get_all_users()
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, f"📢 **ОГОЛОШЕННЯ:**\n\n{message.text}", parse_mode="Markdown")
            count += 1
        except: continue
    await message.answer(f"✅ Розсилка завершена для {count} учнів.")
    await state.clear()

# --- 7. ОСНОВНІ ОБРОБНИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    add_user(message.from_user.id)
    await message.answer(f"Привіт, {message.from_user.first_name}! Вітаємо у боті Гімназії №4 🏫", reply_markup=main_keyboard)

@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    photo_id = get_setting("schedule_id")
    if photo_id:
        await message.answer_photo(photo=photo_id, caption="📅 Актуальний розклад")
    else:
        await message.answer("❌ Розклад не завантажений адміністратором.")

@dp.message(F.text == "🎓 Центр учня")
async def student_center(message: types.Message):
    await message.answer("🎓 Учнівський хаб:", reply_markup=student_keyboard)

@dp.message(F.text == "🔮 Передбачення оцінки")
async def get_prediction(message: types.Message):
    res = random.choice([10, 11, 12, 9, 8, "12 з зірочкою!", "Відпочинок!"])
    await message.answer(f"🔮 Сьогодні твоя оцінка: **{res}**", parse_mode="Markdown")

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
    await message.answer(text, parse_mode="HTML")

# --- 8. FAQ ТА ДОПОМОГА ---
@dp.message(F.text == "❓ Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть розділ:", reply_markup=help_keyboard)

@dp.message(F.text == "📝 FAQ")
async def faq_info(message: types.Message):
    faq_text = (
        "<b>📌 Відповіді на питання:</b>\n\n"
        "⏰ <b>Розклад дзвінків:</b>\n"
        "1 урок: 08:00 - 08:45\n2 урок: 08:55 - 09:40\n3 урок: 09:55 - 10:40\n\n"
        "🛡 <b>Безпека:</b>\n"
        "Під час повітряної тривоги учні слідують в укриття.\n\n"
        "🔐 <b>Щоденник:</b>\n"
        "Логін до E-Journal видає класний керівник."
    )
    await message.answer(faq_text, parse_mode="HTML")

@dp.message(F.text == "🔑 Відновити пароль")
async def reset_password(message: types.Message):
    await message.answer("🔑 Для відновлення доступу зверніться до техпідтримки школи або свого вчителя.")

@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Повернення в меню", reply_markup=main_

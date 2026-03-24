import logging
import asyncio
import os
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiohttp import web

# --- 1. НАЛАШТУВАННЯ БОТА (Всі змінні в одному місці) ---
# На Render додайте змінну оточення BOT_TOKEN з вашим токеном
TOKEN = os.getenv("BOT_TOKEN", "8602310062:AAEHbEKlma1p7oT9yuJFISuqbnolgk-0l9I")
ADMIN_ID = 8635308149  # Ваш ID як адміна

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 2. БАЗА ДАНИХ (SQLite) ---
# Створює файл bot_data.db, щоб зберігати ID фото розкладу
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

# Ініціалізуємо базу при запуску
init_db()

# --- 3. СТАНИ (FSM) ---
# Визначає, що бот чекає від користувача в даний момент
class BotStates(StatesGroup):
    waiting_for_suggestion = State()      # Чекає текст пропозиції
    waiting_for_password_reset = State() # Чекає ПІБ та клас
    # Стани вікторини (по одному на питання)
    quiz_q1 = State()
    quiz_q2 = State()
    quiz_q3 = State()

# --- 4. КЛАВІАТУРИ ---

# Глобальна функція для створення клавіатур варіантів (для вікторини)
def get_quiz_kb(options: list):
    # Кожен варіант буде окремою кнопкою в окремому рядку
    buttons = [[KeyboardButton(text=opt)] for opt in options]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

# Головне меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Розклад 🔔"), KeyboardButton(text="❓ Допомога")],
        [KeyboardButton(text="🎮 Вікторина"), KeyboardButton(text="🏫 Школа")]
    ],
    resize_keyboard=True
)

# Меню допомоги
help_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💡 Залишити пропозицію"), KeyboardButton(text="📝 FAQ")],
        [KeyboardButton(text="🔑 Відновити пароль")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

# Початкове меню вікторини
vik_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🚀 Старт Вікторини"), KeyboardButton(text="⬅️ Назад")]],
    resize_keyboard=True
)

# --- 5. ВЕБ-СЕРВЕР ДЛЯ RENDER ---
# Цей блок потрібен, щоб Render не вимикав бота кожні 5 хвилин
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render передає порт через змінну оточення PORT
    port = int(os.getenv("PORT", 8080)) 
    site = web.TCPSite(runner, "0.0.

import logging
import asyncio
import os
import sqlite3
import random
import google.genai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- 1. НАЛАШТУВАННЯ ---
TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
ADMIN_ID = 8635308149 # Ваш ID

# Створюємо клієнта Gemini (новий синтаксис)
client = genai.Client(api_key=GEMINI_KEY)
# Налаштування ШІ Gemini
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

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

# --- 3. СТАНИ (FSM) ---
class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_broadcast = State()
    waiting_for_ai_question = State()

# --- 4. КЛАВІАТУРИ ---

# Головне меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔔 Розклад 🔔"), KeyboardButton(text="🎓 Центр учня")],
        [KeyboardButton(text="🎮 Вікторина"), KeyboardButton(text="🏫 Про школу")],
        [KeyboardButton(text="❓ Допомога")]
    ],
    resize_keyboard=True
)

# Меню Центру учня
student_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔮 Передбачення оцінки"), KeyboardButton(text="🍎 Меню їдальні")],
        [KeyboardButton(text="🤖 Запитати Gemini"), KeyboardButton(text="💡 Залишити пропозицію")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

# Допомога
help_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 FAQ"), KeyboardButton(text="🔑 Відновити пароль")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)

# Інлайн-клавіатура для вікторини
def get_quiz_kb(step):
    builder = InlineKeyboardBuilder()
    if step == 1:
        builder.row(InlineKeyboardButton(text="1. Перейду", callback_data="quiz_wrong"))
        builder.row(InlineKeyboardButton(text="2. Видалю ✅", callback_data="quiz_step2"))
        builder.row(InlineKeyboardButton(text="3. Перешлю", callback_data="quiz_wrong"))
    elif step == 2:
        builder.row(InlineKeyboardButton(text="1. 1234", callback_data="quiz_wrong"))
        builder.row(InlineKeyboardButton(text="2. qwerty", callback_data="quiz_wrong"))
        builder.row(InlineKeyboardButton(text="3. Tr0n_&_4 ✅", callback_data="quiz_step3"))
    return builder.as_markup()

# --- 5. ВЕБ-СЕРВЕР (Для хостингів типу Render/Replit) ---
async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()

# --- 6. ОБРОБНИКИ (Handlers) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    if state: await state.clear()
    add_user(message.from_user.id)
    await message.answer(f"Привіт, {message.from_user.first_name}! Вітаємо у боті Гімназії №4 🏫", reply_markup=main_keyboard)

# --- АДМІН-ФУНКЦІЇ ---
@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def update_schedule(message: types.Message):
    save_schedule_id(message.photo[-1].file_id)
    await message.answer("✅ Новий розклад збережено у базі!")

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
    await message.answer(f"✅ Розсилка завершена. Отримали: {count} учнів.")
    await state.clear()

# --- РОЗКЛАД ---
@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    photo_id = get_schedule_id()
    if photo_id:
        await message.answer_photo(photo=photo_id, caption="📅 Актуальний розклад занять")
    else:
        await message.answer("❌ Розклад поки не завантажений адміністрацією.")

# --- ЦЕНТР УЧНЯ ---
@dp.message(F.text == "🎓 Центр учня")
async def student_center(message: types.Message):
    await message.answer("🎓 Ласкаво просимо до учнівського хабу!", reply_markup=student_keyboard)

@dp.message(F.text == "🔮 Передбачення оцінки")
async def get_prediction(message: types.Message):
    res = random.choice([10, 11, 12, 9, 8, 7, "12 з зірочкою!", "Відпочинок!"])
    await message.answer(f"🔮 Магічна куля пророкує тобі сьогодні: **{res}**", parse_mode="Markdown")

@dp.message(F.text == "🍎 Меню їдальні")
async def school_menu(message: types.Message):
    await message.answer("🍴 **Сьогодні в меню:**\n• Суп овочевий\n• Плов з м'ясом\n• Компот\n• Свіжа випічка", parse_mode="Markdown")

@dp.message(F.text == "💡 Залишити пропозицію")
async def suggestion_start(message: types.Message, state: FSMContext):
    await message.answer("Напишіть вашу ідею або звернення анонімно:")
    await state.set_state(BotStates.waiting_for_suggestion)

@dp.message(BotStates.waiting_for_suggestion)
async def suggestion_process(message: types.Message, state: FSMContext):
    await bot.send_message(ADMIN_ID, f"📩 **Нова пропозиція:**\n{message.text}")
    await message.answer("✅ Дякуємо! Твою пропозицію передано адміністрації.", reply_markup=student_keyboard)
    await state.clear()

# Gemini AI Помічник
@dp.message(F.text == "🤖 Запитати Gemini")
async def ai_ask(message: types.Message, state: FSMContext):
    await message.answer("Напишіть ваше запитання для ШІ (наприклад: 'Поясни теорему Піфагора'):")
    await state.set_state(BotStates.waiting_for_ai_question)

# Оновлений обробник Gemini
@dp.message(BotStates.waiting_for_ai_question)
async def ai_process(message: types.Message, state: FSMContext):
    msg = await message.answer("🔎 Шукаю відповідь у мізках...")
    try:
        # Новий синтаксис запиту
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=f"Ти помічник учня школи. Відповідай коротко і зрозуміло українською мовою: {message.text}"
        )
        await msg.edit_text(response.text)
    except Exception as e:
        logging.error(f"AI Error: {e}")
        await msg.edit_text("❌ Помилка доступу до ШІ. Перевірте API ключ у налаштуваннях Render.")
    await state.clear()

# --- ВІКТОРИНА ---
@dp.message(F.text == "🎮 Вікторина")
async def quiz_start(message: types.Message):
    await message.answer("🚀 Перевірка знань з кібербезпеки!\n\nПитання 1: Прийшло SMS про виграш. Що зробиш?", 
                         reply_markup=get_quiz_kb(1))

@dp.callback_query(F.data == "quiz_wrong")
async def quiz_wrong(callback: types.CallbackQuery):
    await callback.answer("❌ Неправильно! Спробуй інший варіант.", show_alert=True)

@dp.callback_query(F.data == "quiz_step2")
async def quiz_step2(callback: types.CallbackQuery):
    await callback.message.edit_text("✅ Вірно! Питання 2: Який пароль найнадійніший?", reply_markup=get_quiz_kb(2))

@dp.callback_query(F.data == "quiz_step3")
async def quiz_finish(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("🏆 Перемога! Ти справжній майстер безпеки!", reply_markup=main_keyboard)

# --- ІНШЕ ---
@dp.message(F.text == "🏫 Про школу")
async def school_info(message: types.Message):
    text = "<b>🏫 Гімназія №4 Павлоградської міської ради</b>\n\nвул. Сергія Корольова, 3\n<a href='https://www.sc4.dp.ua/'>Офіційний сайт</a>"
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=False)

@dp.message(F.text == "❓ Допомога")
async def help_menu(message: types.Message):
    await message.answer("Оберіть розділ допомоги:", reply_markup=help_keyboard)

@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Повертаємось у головне меню", reply_markup=main_keyboard)

# --- ЗАПУСК ---
async def main():
    await start_web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот вимкнений")

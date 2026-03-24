import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- ГЛОБАЛЬНА ЗМІННА ДЛЯ РОЗКЛАДУ ---
# Це та сама "комірка", де зберігатиметься ID фото
current_schedule_id = None 

# 1. СТАНИ (FSM)
class BotStates(StatesGroup):
    waiting_for_suggestion = State()
    waiting_for_password_reset = State()

# НАЛАШТУВАННЯ
TOKEN = os.getenv("BOT_TOKEN", "8602310062:AAEHbEKlma1p7oT9yuJFISuqbnolgk-0l9I")
ADMIN_ID = 8635308149

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# АДМІН-КОМАНДА: ОНОВЛЕННЯ РОЗКЛАДУ
@dp.message(F.photo, F.from_user.id == ADMIN_ID)
async def update_schedule_photo(message: types.Message):
    global current_schedule_id  # Кажемо боту використовувати глобальну комірку
    current_schedule_id = message.photo[-1].file_id  # Записуємо нове фото
    
    await message.answer(
        f"✅ <b>Розклад оновлено в пам'яті бота!</b>\n\n"
        f"Тепер при натисканні на кнопку учні бачитимуть це фото.\n"
        f"Його ID: <code>{current_schedule_id}</code>", 
        parse_mode="HTML"
    )

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

# РОЗДІЛ: РОЗКЛАД
@dp.message(F.text == "🔔 Розклад 🔔")
async def send_schedule(message: types.Message):
    global current_schedule_id
    try:
        if current_schedule_id:
            # Якщо адмін надіслав фото в цьому сеансі
            await message.answer_photo(photo=current_schedule_id, caption="📅 Актуальний розклад (оновлено)")
        else:
            # Якщо фото в пам'яті немає — шукаємо файл
            photo = FSInputFile("schedule.jpg")
            await message.answer_photo(photo=photo, caption="📅 Поточний розклад занять (з файлу)")
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("❌ Файл з розкладом не знайдено. Адмін, надішли фото розкладу!")

# РОЗДІЛ: ШКОЛА
@dp.message(F.text == "🏫 Школа")
async def school_info(message: types.Message):
    text = (
        "<b>Гімназія №4 Павлоградської міської ради</b>\n\n"
        "📍 <b>Адреса:</b> вул. Корольова Сергія, 3\n"
        "🔗 <a href='https://sc4.dp.ua/'>Офіційний сайт</a>"
    )
    await message.answer(text, parse_mode="HTML")

# РОЗДІЛ: ВІКТОРИНА
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

# --- FSM (ФОРМИ) ---

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
    await message.answer("<b>FAQ</b>\n\nПитання тут...", parse_mode="HTML")

@dp.message()
async def handle_all(message: types.Message):
    res = RESPONSES.get(message.text)
    if res:
        await message.answer(res)
    else:
        await message.answer("Скористайтеся меню.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import sqlite3
from pyrogram import Client, filters
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАСТРОЙКИ ---
API_ID = 35681900
API_HASH = "e40ccdcad3ea2108a95fdb371ced0ddd"
USER_SESSION = "my_account"
BOT_TOKEN = "8298905952:AAGf0kWp7OEwu0XDAaf9E9v63TZuu6SVUUk"
ADMIN_ID = 842022631
TARGET_CHAT = "me"

# --- БАЗА ДАННЫХ ---
db = sqlite3.connect("config.db")
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS keywords (word TEXT UNIQUE)")
cur.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT UNIQUE)")
db.commit()

# --- БОТ ДЛЯ КОМАНД АДМИНА ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📝 Слова", callback_data="list_words"),
                types.InlineKeyboardButton(text="📢 Каналы", callback_data="list_channels"))
    builder.row(types.InlineKeyboardButton(text="➕ Добавить слово", callback_data="add_word"),
                types.InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel"))
    return builder.as_markup()

@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Управление парсером:", reply_markup=get_main_kb())

@dp.callback_query()
async def callbacks(callback: types.CallbackQuery):
    action = callback.data
    if action == "list_words":
        cur.execute("SELECT word FROM keywords")
        words = [f"• {r[0]}" for r in cur.fetchall()]
        text = "Список слов:\n" + ("\n".join(words) if words else "Пусто")
        # ОБНОВЛЕНИЕ: Проверяем, изменилось ли что-то
        try:
            await callback.message.edit_text(text, reply_markup=get_main_kb())
        except Exception as e:
            if "message is not modified" not in str(e):
                await callback.answer(f"Ошибка: {e}")
    
    elif action == "add_word":
        await callback.message.answer("Введите слова через запятую (например: крипта, акция, скидка):")
        
    elif action == "add_channel":
        await callback.message.answer("Введите @юзернеймы каналов через запятую:")
    
    elif action == "list_channels":
        cur.execute("SELECT username FROM channels")
        channels = [f"• {r[0]}" for r in cur.fetchall()]
        text = "Список каналов:\n" + ("\n".join(channels) if channels else "Пусто")
        try:
            await callback.message.edit_text(text, reply_markup=get_main_kb())
        except Exception as e:
            if "message is not modified" not in str(e):
                await callback.answer(f"Ошибка: {e}")

@dp.message()
async def handle_text(message: types.Message):
    if message.from_user.id != ADMIN_ID: 
        return
    
    # Если в тексте есть @, значит это каналы
    if "@" in message.text:
        items = [i.strip() for i in message.text.split(",")]
        added = 0
        for i in items:
            try:
                cur.execute("INSERT OR IGNORE INTO channels VALUES (?)", (i,))
                if cur.rowcount > 0:
                    added += 1
            except Exception as e:
                print(f"Ошибка добавления канала {i}: {e}")
        db.commit()
        await message.answer(f"✅ Добавлено каналов: {added}")
    # Иначе считаем это словами
    else:
        items = [i.strip().lower() for i in message.text.split(",")]
        added = 0
        for i in items:
            try:
                cur.execute("INSERT OR IGNORE INTO keywords VALUES (?)", (i,))
                if cur.rowcount > 0:
                    added += 1
            except Exception as e:
                print(f"Ошибка добавления слова {i}: {e}")
        db.commit()
        await message.answer(f"✅ Добавлено слов: {added}")

# --- ПАРСЕР ДЛЯ МОНИТОРИНГА КАНАЛОВ ---
user_app = Client(USER_SESSION, api_id=API_ID, api_hash=API_HASH)

@user_app.on_message(filters.text | filters.caption)
async def monitor_channels(client, message):
    cur.execute("SELECT username FROM channels")
    monitored = [r[0] for r in cur.fetchall()]
    
    # Проверяем, из нужного ли канала сообщение
    if message.chat.username and f"@{message.chat.username}" in monitored:
        cur.execute("SELECT word FROM keywords")
        all_keywords = [r[0] for r in cur.fetchall()]
        
        text = (message.text or message.caption).lower()
        if any(word in text for word in all_keywords):
            await message.copy(TARGET_CHAT)

# --- ЗАПУСК ---
async def main():
    print("Запуск системы...")
    
    # Запускаем парсер каналов
    await user_app.start()
    print("Парсер запущен")
    
    # Запускаем бота отдельно, если нужны команды
    # ИЛИ убираем polling полностью и используем вебхуки
    
    # Вместо polling просто держим приложение запущенным
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка...")
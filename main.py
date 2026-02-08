import asyncio
import sqlite3
import threading
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
TARGET_CHAT = "@parserchenalbot"

# --- БАЗА ДАННЫХ ---
# Используем отдельные подключения для безопасности
def get_db_connection():
    """Создаем новое подключение к БД для каждого потока"""
    db = sqlite3.connect("config.db", check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")  # Для лучшей параллельной работы
    return db

# Инициализация таблиц
init_db = get_db_connection()
init_cur = init_db.cursor()
init_cur.execute("CREATE TABLE IF NOT EXISTS keywords (word TEXT UNIQUE)")
init_cur.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT UNIQUE)")
init_db.commit()
init_db.close()

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
    db = get_db_connection()
    cur = db.cursor()
    
    action = callback.data
    if action == "list_words":
        cur.execute("SELECT word FROM keywords")
        words = [f"• {r[0]}" for r in cur.fetchall()]
        text = "Список слов:\n" + ("\n".join(words) if words else "Пусто")
        try:
            await callback.message.edit_text(text, reply_markup=get_main_kb())
        except Exception as e:
            if "message is not modified" not in str(e):
                await callback.answer(f"Ошибка: {e}")
        finally:
            db.close()
    
    elif action == "add_word":
        await callback.message.answer("Введите слова через запятую (например: крипта, акция, скидка):")
        db.close()
        
    elif action == "add_channel":
        await callback.message.answer("Введите @юзернеймы каналов через запятую:")
        db.close()
    
    elif action == "list_channels":
        cur.execute("SELECT username FROM channels")
        channels = [f"• {r[0]}" for r in cur.fetchall()]
        text = "Список каналов:\n" + ("\n".join(channels) if channels else "Пусто")
        try:
            await callback.message.edit_text(text, reply_markup=get_main_kb())
        except Exception as e:
            if "message is not modified" not in str(e):
                await callback.answer(f"Ошибка: {e}")
        finally:
            db.close()

@dp.message()
async def handle_text(message: types.Message):
    if message.from_user.id != ADMIN_ID: 
        return
    
    db = get_db_connection()
    cur = db.cursor()
    
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
    
    db.close()

# --- ПАРСЕР ДЛЯ МОНИТОРИНГА КАНАЛОВ ---
user_app = Client(USER_SESSION, api_id=API_ID, api_hash=API_HASH)

@user_app.on_message(filters.text | filters.caption)
async def monitor_channels(client, message):
    try:
        # Создаем новое подключение к БД
        db = get_db_connection()
        cur = db.cursor()
        
        # Получаем список каналов для мониторинга
        cur.execute("SELECT username FROM channels")
        monitored = [r[0].lower() for r in cur.fetchall()]
        
        # Проверяем, из нужного ли канала сообщение
        if message.chat.username:
            current_channel = f"@{message.chat.username.lower()}"
            
            # ДЕБАГ: выводим информацию
            print(f"Получено сообщение из: {current_channel}")
            print(f"Мониторим каналы: {monitored}")
            
            if current_channel in monitored:
                # Получаем ключевые слова
                cur.execute("SELECT word FROM keywords")
                all_keywords = [r[0].lower() for r in cur.fetchall()]
                
                text = (message.text or message.caption or "").lower()
                
                # ДЕБАГ: выводим текст и ключевые слова
                print(f"Текст сообщения: {text[:100]}...")
                print(f"Ключевые слова: {all_keywords}")
                
                if text and all_keywords:
                    for word in all_keywords:
                        if word in text:
                            print(f"Найдено совпадение: '{word}' в тексте")
                            await message.copy(TARGET_CHAT)
                            print("Сообщение переслано!")
                            break
        
        db.close()
        
    except Exception as e:
        print(f"Ошибка в monitor_channels: {e}")
        import traceback
        traceback.print_exc()

# --- ЗАПУСК ---
async def run_parser():
    """Запуск только парсера"""
    print("Запуск парсера каналов...")
    await user_app.start()
    
    # Получаем информацию о пользователе
    me = await user_app.get_me()
    print(f"Парсер запущен как: @{me.username}")
    print("Ожидание сообщений...")
    
    # Ожидаем сигнал завершения
    await asyncio.Event().wait()

async def run_bot():
    """Запуск только бота для админа"""
    print("Запуск бота админа...")
    await dp.start_polling(bot)

async def main():
    """Запуск обоих компонентов параллельно"""
    print("Запуск системы мониторинга...")
    
    # Создаем задачи для параллельного выполнения
    parser_task = asyncio.create_task(run_parser())
    bot_task = asyncio.create_task(run_bot())
    
    # Ожидаем завершения обеих задач
    await asyncio.gather(parser_task, bot_task)

if __name__ == "__main__":
    try:
        # Добавляем подробное логирование
        import logging
        logging.basicConfig(level=logging.INFO)
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nОстановка системы...")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
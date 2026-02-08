import asyncio
import sqlite3
import logging
from pyrogram import Client, filters
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- НАСТРОЙКИ ---
API_ID = 35681900
API_HASH = "e40ccdcad3ea2108a95fdb371ced0ddd"
USER_SESSION = "my_account"
BOT_TOKEN = "8298905952:AAGf0kWp7OEwu0XDAaf9E9v63TZuu6SVUUk"
ADMIN_ID = 842022631
TARGET_CHAT = "me"

# --- БАЗА ДАННЫХ ---
def get_db_connection():
    db = sqlite3.connect("config.db", check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    return db

# Инициализация БД
def init_database():
    db = get_db_connection()
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS keywords (word TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS channels (username TEXT UNIQUE)")
    db.commit()
    db.close()
    logger.info("База данных инициализирована")

init_database()

# --- БОТ ДЛЯ АДМИНА (БЕЗ POLLING) ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_main_kb():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📝 Слова", callback_data="list_words"),
                types.InlineKeyboardButton(text="📢 Каналы", callback_data="list_channels"))
    builder.row(types.InlineKeyboardButton(text="➕ Добавить слово", callback_data="add_word"),
                types.InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel"))
    return builder.as_markup()

# --- ОБРАБОТЧИКИ ДЛЯ БОТА ---
# (здесь ваши обработчики @dp.message, @dp.callback_query как были)

# --- ПАРСЕР ДЛЯ МОНИТОРИНГА КАНАЛОВ ---
user_app = Client(USER_SESSION, api_id=API_ID, api_hash=API_HASH)

# Глобальная переменная для состояния бота
bot_initialized = False

async def send_admin_notification(text: str):
    """Отправка уведомления админу"""
    try:
        await bot.send_message(ADMIN_ID, text)
        logger.info(f"Уведомление отправлено: {text}")
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")

async def handle_bot_commands():
    """Обработка команд бота через long polling вручную"""
    global bot_initialized
    
    if not bot_initialized:
        await send_admin_notification("✅ Парсер каналов запущен!\n"
                                     "Используйте /start для управления")
        bot_initialized = True
    
    offset = 0
    while True:
        try:
            # Получаем обновления вручную
            updates = await bot.get_updates(offset=offset, timeout=30)
            
            for update in updates:
                offset = update.update_id + 1
                
                # Обрабатываем сообщения
                if update.message:
                    await dp.feed_update(bot, update)
                
                # Обрабатываем callback-запросы
                if update.callback_query:
                    await dp.feed_update(bot, update)
                    
        except Exception as e:
            logger.error(f"Ошибка в handle_bot_commands: {e}")
            await asyncio.sleep(5)

@user_app.on_message(filters.text | filters.caption)
async def monitor_channels(client, message):
    try:
        db = get_db_connection()
        cur = db.cursor()
        
        # Получаем список каналов
        cur.execute("SELECT username FROM channels")
        monitored = [r[0].lower() for r in cur.fetchall()]
        
        if message.chat.username:
            current_channel = f"@{message.chat.username.lower()}"
            
            if current_channel in monitored:
                cur.execute("SELECT word FROM keywords")
                all_keywords = [r[0].lower() for r in cur.fetchall()]
                
                text = (message.text or message.caption or "").lower()
                
                if text and all_keywords:
                    for word in all_keywords:
                        if word in text:
                            logger.info(f"Найдено '{word}' в {current_channel}")
                            await message.copy(TARGET_CHAT)
                            break
        
        db.close()
        
    except Exception as e:
        logger.error(f"Ошибка в monitor_channels: {e}")

# --- АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ: ЗАПУСК ТОЛЬКО ПАРСЕРА ---
async def main_parser_only():
    """Запуск ТОЛЬКО парсера, без бота для команд"""
    logger.info("Запуск парсера каналов...")
    
    await user_app.start()
    me = await user_app.get_me()
    logger.info(f"Парсер запущен как: @{me.username}")
    
    # Отправляем приветственное сообщение
    try:
        await bot.send_message(
            ADMIN_ID,
            "🔍 Парсер каналов запущен!\n\n"
            "Для управления используйте:\n"
            "• Добавить канал: /add_channel @username\n"
            "• Добавить слово: /add_word ключевое_слово\n"
            "• Список каналов: /channels\n"
            "• Список слов: /words"
        )
    except:
        pass
    
    # Простая обработка команд через Pyrogram
    @user_app.on_message(filters.command("start") & filters.user(ADMIN_ID))
    async def start_command(client, message):
        await message.reply("Парсер активен! Используйте команды:\n"
                          "/add_channel - добавить канал\n"
                          "/add_word - добавить слово\n"
                          "/channels - список каналов\n"
                          "/words - список слов")
    
    @user_app.on_message(filters.command("add_channel") & filters.user(ADMIN_ID))
    async def add_channel_command(client, message):
        args = message.text.split()
        if len(args) > 1:
            db = get_db_connection()
            for channel in args[1:]:
                if channel.startswith("@"):
                    db.execute("INSERT OR IGNORE INTO channels VALUES (?)", (channel,))
            db.commit()
            db.close()
            await message.reply("✅ Каналы добавлены")
    
    # ... другие команды
    
    # Ждем сигнала завершения
    await asyncio.Event().wait()

# --- ГЛАВНЫЙ ЗАПУСК ---
async def main():
    """Выберите один из вариантов запуска"""
    
    # ВАРИАНТ 1: Только парсер с простыми командами
    await main_parser_only()
    
    # ВАРИАНТ 2: Парсер + бот (если нужно)
    # await asyncio.gather(
    #     user_app.start(),
    #     handle_bot_commands()
    # )

if __name__ == "__main__":
    try:
        # Убиваем возможные предыдущие процессы
        import os
        import signal
        os.system("pkill -f 'python.*bot' 2>/dev/null || true")
        
        logger.info("=" * 50)
        logger.info("Запуск системы мониторинга Telegram")
        logger.info("=" * 50)
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("Система остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
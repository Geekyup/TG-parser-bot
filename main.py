from pyrogram import Client, filters

# --- НАСТРОЙКИ ---
api_id = 28181900          
api_hash = "e40ccdcad3ea2108a95fdb371ced0ddd"      
keywords = ["акция", "крипта", "вакансия", "путин", 'россия', "рф", "зумеры"] 
target_chat = "me"        

app = Client("my_account", api_id=api_id, api_hash=api_hash)

# Добавляем фильтр group и channel, чтобы юзербот гарантированно слушал всё
@app.on_message((filters.group | filters.channel) & (filters.text | filters.caption))
async def check_keywords(client, message):
    # 1. Извлекаем текст
    content = message.text or message.caption
    if not content:
        return

    # 2. Приводим к нижнему регистру для сравнения
    text = content.lower()
    
    # 3. Проверка ключевых слов (используем генератор для скорости)
    if any(word.lower() in text for word in keywords):
        try:
            # Информация об источнике
            chat_title = message.chat.title or "Группа без названия"
            
            # Формируем красивую ссылку
            link = message.link if message.link else "Ссылка недоступна"
            
            header = (
                f"<b>🔍 Найдено совпадение!</b>\n"
                f"<b>Источник:</b> {chat_title}\n"
                f"<b>Ссылка:</b> <a href='{link}'>Перейти к сообщению</a>\n"
                f"--------------------------"
            )

            # Отправляем уведомление
            await client.send_message(target_chat, header, disable_web_page_preview=True)
            # Копируем сообщение
            await message.copy(target_chat) 
            
            print(f"✅ Найдено и переслано из: {chat_title}")
            
        except Exception as e:
            print(f"❌ Ошибка при пересылке: {e}")

# Добавим обработчик ошибок запуска, если сессия занята
print("🚀 Парсер запущен и мониторит все ваши подписки...")
app.run()

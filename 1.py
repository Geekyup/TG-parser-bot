from pyrogram import Client, filters

# --- НАСТРОЙКИ ---
api_id = 35681900          # Твой API_ID
api_hash = "e40ccdcad3ea2108a95fdb371ced0ddd"      # Твой API_HASH
keywords = ["акция", "крипта", "вакансия"] 
target_chat = "@parserchenalbot"        # Куда слать результат

# Если оставить пустой список, будет мониторить ВСЕ твои чаты и каналы
# Если вписать id, то только конкретные
source_channels = [] 

app = Client("my_account", api_id=api_id, api_hash=api_hash)

@app.on_message(filters.text | filters.caption) # Слушаем текст и подписи к фото
async def check_keywords(client, message):
    # Получаем текст из сообщения или подписи к медиа
    content = message.text or message.caption
    if not content:
        return

    text = content.lower()
    
    # Ищем ключевые слова
    if any(word.lower() in text for word in keywords):
        try:
            # Пересылаем сообщение
            await message.forward(target_chat)
            print(f"✅ Найдено в: {message.chat.title or 'Личке'}")
        except Exception as e:
            print(f"❌ Ошибка пересылки: {e}")

print("🚀 Парсер запущен и слушает сообщения...")
app.run()
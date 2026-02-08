from pyrogram import Client, filters

# --- НАСТРОЙКИ ---
api_id = 28181900          # Твой API_ID
api_hash = "e40ccdcad3ea2108a95fdb371ced0ddd"      # Твой API_HASH
keywords = ["акция", "крипта", "вакансия", "путин", 'Россия', "РФ", "зумеры"] 
target_chat = "me"        

app = Client("my_account", api_id=api_id, api_hash=api_hash)

@app.on_message(filters.text | filters.caption)
async def check_keywords(client, message):
    content = message.text or message.caption
    if not content:
        return

    text = content.lower()
    
    # Проверка ключевых слов
    if any(word.lower() in text for word in keywords):
        try:
            # Формируем информацию об источнике
            chat_title = message.chat.title or "Личные сообщения"
            chat_id = message.chat.id
            
            # Ссылка на сообщение (работает для публичных и большинства приватных групп)
            link = message.link if message.link else f"tg://user?id={chat_id}"
            
            # Текст-заголовок
            header = f"<b>🔍 Найдено совпадение!</b>\n" \
                     f"<b>Источник:</b> {chat_title}\n" \
                     f"<b>Ссылка:</b> <a href='{link}'>Перейти к сообщению</a>\n" \
                     f"--------------------------\n"

            # Отправляем сначала уведомление, а потом само сообщение (копией)
            await client.send_message(target_chat, header, disable_web_page_preview=True)
            await message.copy(target_chat) 
            
            print(f"✅ Найдено в: {chat_title}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")

print("🚀 Парсер запущен...")
app.run()
import asyncio
from pyrogram import Client
from pyrogram.raw import types
from pyrogram.raw.functions.messages import GetHistory
from pyrogram.enums import ChatType

api_id = 28181900
api_hash = "e40ccdcad3ea2108a95fdb371ced0ddd"

keywords = ["акция", "крипта", "вакансия", "путин", "россия", "рф", "зумеры"]
target_chat = "me"
processed = set()

app = Client("my_account", api_id=api_id, api_hash=api_hash)


def match_keywords(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in keywords)


@app.on_raw_update()
async def raw_handler(client, update, users, chats):
    if isinstance(update, types.UpdateNewChannelMessage):
        msg = update.message
        if not hasattr(msg, 'message') or not msg.message:
            return

        text = msg.message
        
        # Исправлено: правильное получение channel_id
        if isinstance(msg.peer_id, types.PeerChannel):
            channel_id = msg.peer_id.channel_id
        else:
            return
            
        msg_id = (channel_id, msg.id)

        if msg_id in processed:
            return

        if match_keywords(text):
            try:
                # Исправлено: преобразование channel_id в правильный формат
                chat_id = int(f"-100{channel_id}")
                await client.forward_messages(target_chat, chat_id, msg.id)
                processed.add(msg_id)
                print(f"RAW → forwarded: {text[:50]}")
            except Exception as e:
                print(f"RAW error: {e}")


async def polling_loop():
    await asyncio.sleep(5)  # Даём время на подключение
    
    while True:
        try:
            async for dialog in app.get_dialogs():
                # Исправлено: правильная проверка типа чата
                if dialog.chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                    continue

                chat_id = dialog.chat.id

                try:
                    async for msg in app.get_chat_history(chat_id, limit=3):
                        if not msg.text:
                            continue

                        msg_id = (chat_id, msg.id)

                        if msg_id in processed:
                            continue

                        if match_keywords(msg.text):
                            try:
                                await msg.forward(target_chat)
                                processed.add(msg_id)
                                print(f"POLL → forwarded from {dialog.chat.title}: {msg.text[:50]}")
                            except Exception as e:
                                print(f"POLL error in {dialog.chat.title}: {e}")
                                
                except Exception as e:
                    print(f"Error getting history from {dialog.chat.title}: {e}")
                    continue

            await asyncio.sleep(15)

        except Exception as e:
            print(f"Polling crash: {e}")
            await asyncio.sleep(5)


async def main():
    await app.start()
    print("✓ Userbot started (RAW + POLLING)")
    
    # Запускаем polling в фоне
    task = asyncio.create_task(polling_loop())
    
    try:
        await asyncio.Event().wait()  # Ждём бесконечно
    except KeyboardInterrupt:
        print("\n✓ Stopping...")
        task.cancel()
        await app.stop()


if __name__ == "__main__":
    app.run(main())
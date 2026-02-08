import asyncio
from pyrogram import Client
from pyrogram.raw import types

api_id = 28181900
api_hash = "e40ccdcad3ea2108a95fdb371ced0ddd"

keywords = ["акция", "крипта", "вакансия", "путин", "россия", "рф", "зумеры"]
target_chat = "me"

app = Client("stable_userbot", api_id=api_id, api_hash=api_hash)

# Храним последние обработанные сообщения (чтобы не было дублей)
processed = set()


def match_keywords(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in keywords)


# ================= RAW LISTENER =================
@app.on_raw_update()
async def raw_handler(client, update, users, chats):
    if isinstance(update, types.UpdateNewChannelMessage):
        msg = update.message

        if not msg.message:
            return

        text = msg.message
        msg_id = (msg.peer_id.channel_id, msg.id)

        if msg_id in processed:
            return

        if match_keywords(text):
            try:
                await client.forward_messages(
                    target_chat,
                    msg.peer_id.channel_id,
                    msg.id
                )
                processed.add(msg_id)
                print("RAW → forwarded")

            except Exception as e:
                print("RAW error:", e)


# ================= POLLING FALLBACK =================
async def polling_loop():
    await app.start()

    while True:
        try:
            async for dialog in app.get_dialogs():
                if dialog.chat.type != "channel":
                    continue

                chat_id = dialog.chat.id

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
                            print("POLL → forwarded from", dialog.chat.title)

                        except Exception as e:
                            print("POLL error:", e)

            await asyncio.sleep(15)  # интервал polling

        except Exception as e:
            print("Polling crash:", e)
            await asyncio.sleep(5)


# ================= START =================
async def main():
    async with app:
        print("Userbot started (RAW + POLLING)")
        await polling_loop()


asyncio.run(main())
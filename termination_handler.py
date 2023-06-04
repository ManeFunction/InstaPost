from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

login = os.environ.get("LOGIN")
appid = os.environ.get("APPID")
apihash = os.environ.get("APIHASH")
session_string = os.environ.get("SESSION_STRING")
log_tg_channel = int(os.environ.get("LOG_TG_CHANNEL"))


async def send_telegram_message(message):
    async with TelegramClient(StringSession(session_string), appid, apihash) as client:
        await client.send_message(log_tg_channel, message)


def log_to_telegram(message):
    asyncio.run(send_telegram_message(message))


print("Termination signal was caught. SENDING ALARMS!")
log_to_telegram(f"⛔️ **{login}** was terminated!")

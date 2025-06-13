# telegram_bot.py

import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hcode
import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from dotenv import load_dotenv

# --- Загружаем переменные окружения ---
load_dotenv()

# --- Конфигурация ---
AGENT_API_URL = "http://localhost:8000/query"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelegramBot")

# --- Инициализация бота ---
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# --- Повторные попытки подключения к агенту ---
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    reraise=True
)
async def send_to_agent(user_input: str) -> dict:
    """Отправляет запрос в MCP-агент с retry и таймаутами"""
    async with httpx.AsyncClient(timeout=20.0) as client:
        logger.debug(f"Sending to agent: {user_input}")
        response = await client.post(AGENT_API_URL, json={"user_input": user_input})
        response.raise_for_status()
        return response.json()


@dp.message()
async def handle_message(message: Message):
    user_input = message.text
    logger.info(f"Получено от пользователя: {user_input}")

    try:
        reply_data = await send_to_agent(user_input)
        reply_text = reply_data.get("reply", "Нет ответа")
    except httpx.HTTPStatusError as e:
        logger.error(f"Ошибка сервера при запросе к агенту: {e.response.status_code} - {e.response.text()}")
        reply_text = f"Ошибка сервера: {e.response.status_code}"
    except httpx.ReadTimeout:
        logger.warning("Таймаут при ожидании ответа от агента")
        reply_text = "Сервер слишком долго не отвечает"
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}", exc_info=True)
        reply_text = "Произошла внутренняя ошибка"

    await message.reply(hcode(reply_text))


async def main():
    logger.info("Запуск Telegram-бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
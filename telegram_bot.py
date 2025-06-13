# telegram_bot.py

import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hcode
import httpx

# === Настройки ===
TELEGRAM_BOT_TOKEN = "7220147586:AAFCOP2u1ROzCC8uvVt-xb4iv42KGYyxo1c"
AGENT_API_URL = "http://localhost:8000/query"

# === Логирование ===
logging.basicConfig(level="INFO")
logger = logging.getLogger("TelegramBot")


bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@dp.message()
async def handle_message(message: Message):
    user_input = message.text
    logger.info(f"Received from Telegram: {user_input}")

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(AGENT_API_URL, json={"user_input": user_input})
            if res.status_code == 200:
                data = res.json()
                reply = data.get("reply", "Нет ответа")
            else:
                reply = f"Ошибка: {res.status_code}"
        except Exception as e:
            reply = f"Ошибка подключения: {str(e)}"

    await message.reply(hcode(reply))


async def main():
    logger.info("Starting Telegram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

# from aiogram import Bot, Dispatcher, types
# from aiogram.types import Message
# from aiogram.enums import ParseMode
# from aiogram.utils.markdown import hcode
# import asyncio

# # Импортируем асинхронную версию route_input
# from host import route_input  # должен быть async def

# TOKEN = "7220147586:AAFCOP2u1ROzCC8uvVt-xb4iv42KGYyxo1c"

# bot = Bot(token=TOKEN)
# dp = Dispatcher()

# @dp.message()
# async def handle_message(message: Message):
#     user_input = message.text
#     try:
#         # Теперь route_input — async функция, вызываем с await
#         reply = await route_input(user_input)
#         await message.reply(hcode(reply))
#     except Exception as e:
#         await message.reply(hcode(f"Ошибка: {str(e)}"))

# async def main():
#     await dp.start_polling(bot)

# if __name__ == "__main__":
#     asyncio.run(main())

# # from aiogram import Bot, Dispatcher, types
# # from aiogram.types import Message
# # from aiogram.enums import ParseMode
# # from aiogram.utils.markdown import hcode
# # import asyncio
# # from host import route_input

# # TOKEN = "7220147586:AAFCOP2u1ROzCC8uvVt-xb4iv42KGYyxo1c"

# # #bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
# # bot = Bot(token=TOKEN)
# # dp = Dispatcher()

# # @dp.message()
# # async def handle_message(message: Message):
# #     user_input = message.text
# #     reply = route_input(user_input)
# #     await message.reply(hcode(reply))

# # async def main():
# #     await dp.start_polling(bot)

# # if __name__ == "__main__":
# #     asyncio.run(main())

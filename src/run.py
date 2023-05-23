from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import KeyboardButton

from datetime import datetime

import aiosqlite as sq
import asyncio
import nest_asyncio

import src.config as config

from src.bot import MessageHandler
from src.data_managers import UsersData

nest_asyncio.apply()


async def main():
    tg_bot = Bot(token=config.TOKEN)
    dp = Dispatcher(tg_bot)

    async with asyncio.TaskGroup() as tg:
        async with sq.connect("data.db") as con:
            data = UsersData()
            await data.init(con)

            bot = MessageHandler()
            await bot.init(tg, data, con)

            @dp.message_handler(commands=["start"])
            async def start_message(message: types.Message):
                await bot.start_message(message)

            @dp.message_handler(commands=["recreate", "кускуфеу"])
            async def recreate_message(message: types.Message):
                await bot.recreate_message(message)

            @dp.message_handler(commands=["help", "рудз"])
            async def help_message(message: types.Message):
                await bot.help_message(message)

            @dp.message_handler()
            async def reply_message(message: types.Message):
                await bot.reply_message(message)

            executor.start_polling(dp, skip_updates=True)

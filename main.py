from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import KeyboardButton

import aiosqlite as sq
import asyncio
import nest_asyncio

import config
import messages

nest_asyncio.apply()

class DoubleInitError(Exception):
    """Raised when object is initilized for the second time when it shouldn't"""
    pass

class UsersData:
    """Uses async SQLite to storage and manipulate data of users. (Singleton)

    Methods

    init():
        initializes (connects to) a database
    create():
        creates a database if it doesn't exist
    delete():
        deletes a database if it exists
    add_user(user_id):
        adds a user to database if it was not added before
    set_value(user_id, name, new_value):
        changes value of field 'name' of user 'user_id' to 'new_value'
    add_value(user_id, name, delta):
        adds 'delta' to value 'name' of user 'user_id'
    get_value(name, value, result):
        returns value of 'result' of user with 'name' = 'value'
    exists(name, value):
        returns user_id of user with 'name' = 'value', 0 otherwise
    """

    _cur = None

    async def init(self, connection):
        """Initializes and creates database (or connects if it already exists)"""

        connection.row_factory = sq.Row
        self._cur = await connection.cursor()
        await self.create()

    async def create(self):
        """Creates new database if it doesn't exists"""

        await self._cur.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0
            )""")

        await self._cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0
            )""")

    async def delete(self):
        """Deletes database if it exists"""

        await self._cur.execute("""DROP TABLE IF EXISTS users""")
        await self._cur.execute("""DROP TABLE IF EXISTS transactions""")

    async def add_user(self, user_id):
        """Adds user to database
        Raises DoubleInitError if user already exists
        """

        try:
            await self._cur.execute(f"""INSERT INTO users (user_id) VALUES ({user_id})""")
        except Exception as e:
            raise DoubleInitError

    async def set_value(self, user_id, name, new_value):
        """Changes value of 'name' of user 'user_id' to 'new_value'
        Creates new user if it is not added to database
        """

        try:
            await self._cur.execute(f"""INSERT INTO users (user_id, {name}) 
                VALUES ({user_id}, {new_value})""")
        except Exception:
            await self._cur.execute(f"""UPDATE users SET {name} = {new_value} 
                WHERE user_id = {user_id}""")

    async def add_value(self, user_id, name, delta):
        """Adds 'delta' to value 'name' of user 'user_id'
        Creates new user if it is not added to database
        """

        old_value = None
        try: 
            old_value = await self.get_value("user_id", user_id, name)
        except KeyError:
            old_value = 0 

        await self.set_value(user_id, name, old_value + delta)

    async def get_value(self, name, value, result):
        """Returns value of 'result' of user with 'name' = 'value'
        Raises KeyError if not found
        """

        await self._cur.execute(f"""SELECT {result} FROM users 
            WHERE {name} = {value}""")

        result = await self._cur.fetchone()
        if result is None:
            raise KeyError
        return result[0]

    async def exists(self, name, value):
        """Returns user_id of user with 'name' = 'value', 0 otherwise"""

        try:
            result = await self.get_value(name, value, "user_id")
            return result
        except KeyError:
            return 0



def isfloat(number):
    try:
        float(number)
        return True
    except ValueError:
        return False

def add_transaction_check(tokens):
    return len(tokens) == 2 and tokens[0] == "добавить" and isfloat(tokens[1])

def get_balance_check(tokens):
    return len(tokens) == 1 and tokens[0] == "баланс"



async def main():
    bot = Bot(token=config.TOKEN)
    dp = Dispatcher(bot)

    async with asyncio.TaskGroup() as tg:
        async with sq.connect("data.db") as con:
            data = UsersData()
            await data.init(con)


            @dp.message_handler(commands=['start'])
            async def start_message(message: types.Message):
                await message.reply(messages.START)

            @dp.message_handler(commands=["get_id"])
            async def get_id_message(message: types.Message):
                user_id = message.from_user.id
                await message.reply(messages.GET_ID.format(user_id=user_id))


            @dp.message_handler(commands=["register"])
            async def registration_message(message: types.Message):
                user_id = message.from_user.id

                try: 
                    await data.add_user(user_id)
                    await bot.send_message(message.from_user.id, 
                            messages.SUCCESSFUL_REGISTRATION)
                except DoubleInitError:
                    await bot.send_message(message.from_user.id, 
                            messages.DOUBLE_REGISTRATION)

                await con.commit()

            @dp.message_handler(commands=["recreate"])
            async def recreate_message(message: types.Message):
                await data.delete()
                await data.create()

                tg.create_task(bot.send_message(message.from_user.id, messages.RECREATE_DONE,
                        reply_markup=ReplyKeyboardRemove()))
                tg.create_task(con.commit())


            @dp.message_handler(commands=["help"])
            async def help_message(message: types.Message):
                kb = [
                    [KeyboardButton(text="/get_id")],
                    [KeyboardButton(text="/recreate")],
                    [KeyboardButton(text="/register")],
                    [KeyboardButton(text="баланс")]
                ]
                keyboard = ReplyKeyboardMarkup(keyboard=kb)

                await message.reply(messages.HELP, reply_markup=keyboard)

            @dp.message_handler()
            async def message_reply(message: types.Message):
                user_id = message.from_user.id
                result = await data.exists("user_id", user_id)
                if not result:
                    await message.reply(messages.REGISTER_REQUIRED)
                    return

                tokens = [word.lower() for word in message.text.split()]

                if add_transaction_check(tokens):
                    await data.add_value(message.from_user.id, "balance", 
                            round(float(tokens[1]), 2))
                    tg.create_task(message.reply(messages.TRANSACTION_ADDED))
                elif get_balance_check(tokens):
                    balance = await data.get_value("user_id", user_id, "balance")
                    tg.create_task(message.reply(
                            messages.CURRENT_BALANCE.format(balance=balance))
                    )
                else:
                    tg.create_task(message.reply(messages.UNKNOWN_COMMAND))
                tg.create_task(con.commit())


            executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())

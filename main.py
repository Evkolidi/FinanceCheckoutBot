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
            user_id INTEGER PRIMARY KEY
            )""")

        await self._cur.execute("""CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            name TEXT NOT NULL
            )""")

        await self._cur.execute("""CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            name TEXT NOT NULL
            )""")

        await self._cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            amount INTEGER NOT NULL
            )""")

    async def delete(self):
        """Deletes database if it exists"""

        await self._cur.execute("""DROP TABLE IF EXISTS users""")
        await self._cur.execute("""DROP TABLE IF EXISTS accounts""")
        await self._cur.execute("""DROP TABLE IF EXISTS categories""")
        await self._cur.execute("""DROP TABLE IF EXISTS transactions""")

    async def add_user(self, user_id):
        """Adds user to database
        Raises DoubleInitError if user already exists
        """

        try:
            await self._cur.execute("""INSERT INTO users (user_id) VALUES (?)""", (user_id,))
            return True
        except Exception:
            return False

    async def set_value(self, user_id, name, new_value):
        """Changes value of 'name' of user 'user_id' to 'new_value'
        Creates new user if it is not added to database
        """

        try:
            await self._cur.execute("""INSERT INTO users (user_id, ?) 
                VALUES (?, ?)""",
                (name, user_id, new_value))
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

    async def exists_user(self, user_id):
        await self._cur.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,))

        result = await self._cur.fetchone()
        if result is None:
            return False
        return True

    async def get_category_id(self, user_id, category_name):
        await self._cur.execute("""SELECT category_id FROM categories
                WHERE (owner_id, name) = (?, ?)""",
                (user_id, category_name))

        result = await self._cur.fetchone()
        if result is None:
            return -1
        return result[0]

    async def get_account_id(self, user_id, account_name):
        await self._cur.execute("""SELECT account_id FROM accounts
                WHERE (owner_id, name) = (?, ?)""",
                (user_id, account_name))

        result = await self._cur.fetchone()
        if result is None:
            return -1
        return result[0]

    async def exists_category(self, user_id, category_name):
        result = await self.get_category_id(user_id, category_name)
        return result != -1

    async def exists_account(self, user_id, account_name):
        result = await self.get_account_id(user_id, account_name)
        return result != -1

    async def get_balance(self, user_id, account_name=""):
        if account_name:
            await self._cur.execute("""SELECT count(amount), sum(amount) FROM transactions
                    JOIN accounts ON transactions.account_id = accounts.account_id
                    WHERE (accounts.owner_id, accounts.name) = (?, ?)""",
                    (user_id, account_name))
        else:
            await self._cur.execute("""SELECT count(amount), sum(amount) FROM transactions
                    JOIN accounts ON transactions.account_id = accounts.account_id
                    WHERE accounts.owner_id = ?""",
                    (user_id,))

        result = await self._cur.fetchone()
        return result[1] if result[0] else 0

    async def add_category(self, user_id, name):
        exists = await self.exists_category(user_id, name)
        if exists:
            return False

        await self._cur.execute("""INSERT INTO categories (owner_id, name) 
                VALUES (?, ?)""",
                (user_id, name))
        return True

    async def add_account(self, user_id, name):
        exists = await self.exists_account(user_id, name)
        if exists:
            return False

        await self._cur.execute("""INSERT INTO accounts (owner_id, name) 
                VALUES (?, ?)""",
                (user_id, name))
        return True

    async def add_transaction(self, user_id, amount, category_id, account_id):
        await self._cur.execute("""INSERT INTO transactions 
                (category_id, account_id, amount)
                VALUES (?, ?, ?)""",
                (category_id, account_id, amount))



def isfloat(number):
    try:
        float(number)
        return True
    except ValueError:
        return False


async def main():
    bot = Bot(token=config.TOKEN)
    dp = Dispatcher(bot)

    async with asyncio.TaskGroup() as tg:
        async with sq.connect("data.db") as con:
            data = UsersData()
            await data.init(con)


            @dp.message_handler(commands=["start"])
            async def start_message(message: types.Message):
                await message.reply(messages.START)

            @dp.message_handler(commands=["get_id"])
            async def get_id_message(message: types.Message):
                user_id = message.from_user.id

                await message.reply(messages.GET_ID.format(user_id=user_id), 
                        parse_mode=types.ParseMode.HTML)


            @dp.message_handler(commands=["register"])
            async def registration_message(message: types.Message):
                user_id = message.from_user.id

                result = await data.add_user(user_id)

                if result:
                    tg.create_task(bot.send_message(message.from_user.id,
                            messages.SUCCESSFUL_REGISTRATION))
                else:
                    tg.create_task(bot.send_message(message.from_user.id,
                            messages.DOUBLE_REGISTRATION))

                tg.create_task(con.commit())

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

                await message.reply(messages.HELP, reply_markup=keyboard,
                        parse_mode=types.ParseMode.HTML)

            @dp.message_handler()
            async def message_reply(message: types.Message):
                user_id = message.from_user.id
                result = await data.exists_user(user_id)
                if not result:
                    await message.reply(messages.REGISTER_REQUIRED)
                    return

                tokens = [word.lower() for word in message.text.split()]

                match tokens:
                    case "добавить"|"доб", "категорию"|"кат", name:
                        result = await data.add_category(user_id, name)
                        if not result:
                            tg.create_task(message.reply(
                                    messages.DOUBLE_CATEGORY_ADD.format(name=name),
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            tg.create_task(message.reply(
                                    messages.SUCCESSFUL_CATEGORY_ADD.format(name=name),
                                    parse_mode=types.ParseMode.HTML))

                    case "добавить"|"доб", "счет"|"счёт", name:
                        result = await data.add_account(user_id, name)
                        if not result:
                            tg.create_task(message.reply(
                                    messages.DOUBLE_ACCOUNT_ADD.format(name=name),
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            tg.create_task(message.reply(
                                    messages.SUCCESSFUL_ACCOUNT_ADD.format(name=name),
                                    parse_mode=types.ParseMode.HTML))

                    case amount, category, account if isfloat(amount.replace(',', '.')):
                        category_id = await data.get_category_id(user_id, category)
                        account_id = await data.get_account_id(user_id, account)

                        match category_id, account_id:
                            case -1, -1:
                                tg.create_task(message.reply(
                                        messages.CATEGORY_AND_ACCOUNT_NOT_EXIST.format(
                                        category=category, account=account),
                                        parse_mode=types.ParseMode.HTML))
                            case -1, _:
                                tg.create_task(message.reply(
                                        messages.CATEGORY_NOT_EXIST.format(name=category),
                                        parse_mode=types.ParseMode.HTML))
                            case _, -1:
                                tg.create_task(message.reply(
                                        messages.ACCOUNT_NOT_EXIST.format(name=account),
                                        parse_mode=types.ParseMode.HTML))
                            case _, _:
                                await data.add_transaction(user_id, 
                                        float(amount.replace(',', '.')), category_id, account_id)
                                tg.create_task(message.reply(
                                        messages.TRANSACTION_ADD.format(amount=amount, 
                                            category=category, account=account),
                                        parse_mode=types.ParseMode.HTML))

                    case "баланс"|"бал", account:
                        exists = await data.exists_account(user_id, account)
                        if not exists:
                            tg.create_task(message.reply(
                                    messages.ACCOUNT_NOT_EXIST.format(name=account),
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            balance = await data.get_balance(user_id, account)
                            tg.create_task(message.reply(
                                    messages.ACCOUNT_BALANCE.format(balance=round(balance, 2),
                                        account=account), 
                                    parse_mode=types.ParseMode.HTML))

                    case "баланс"|"бал",:
                        balance = await data.get_balance(user_id)
                        tg.create_task(message.reply(
                                messages.BALANCE.format(balance=round(balance, 2)),
                                parse_mode=types.ParseMode.HTML))

                    case _:
                        tg.create_task(message.reply(messages.UNKNOWN_COMMAND))

                tg.create_task(con.commit())


            executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())

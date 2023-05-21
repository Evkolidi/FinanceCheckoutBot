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
    _cur = None

    async def init(self, connection):
        connection.row_factory = sq.Row
        self._cur = await connection.cursor()
        await self.create()

    async def create(self):
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
        await self._cur.execute("""DROP TABLE IF EXISTS users""")
        await self._cur.execute("""DROP TABLE IF EXISTS accounts""")
        await self._cur.execute("""DROP TABLE IF EXISTS categories""")
        await self._cur.execute("""DROP TABLE IF EXISTS transactions""")

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

    async def get_category_id(self, user_id, category_name):
        await self._cur.execute("""SELECT category_id FROM categories
                WHERE (owner_id, name) = (?, ?)""",
                (user_id, category_name))

        result = await self._cur.fetchone()
        return -1 if result is None else result[0]

    async def get_account_id(self, user_id, account_name):
        await self._cur.execute("""SELECT account_id FROM accounts
                WHERE (owner_id, name) = (?, ?)""",
                (user_id, account_name))

        result = await self._cur.fetchone()
        return -1 if result is None else result[0]

    async def exists_user(self, user_id):
        await self._cur.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,))

        result = await self._cur.fetchone()
        return result is not None

    async def exists_category(self, user_id, category_name):
        result = await self.get_category_id(user_id, category_name)
        return result != -1

    async def exists_account(self, user_id, account_name):
        result = await self.get_account_id(user_id, account_name)
        return result != -1

    async def add_user(self, user_id):
        await self._cur.execute("""INSERT INTO users (user_id) VALUES (?)""", (user_id,))

    async def add_category(self, user_id, name):
        await self._cur.execute("""INSERT INTO categories (owner_id, name) 
                VALUES (?, ?)""",
                (user_id, name))

    async def add_account(self, user_id, name):
        await self._cur.execute("""INSERT INTO accounts (owner_id, name) 
                VALUES (?, ?)""",
                (user_id, name))

    async def add_transaction(self, user_id, amount, category_id, account_id):
        await self._cur.execute("""INSERT INTO transactions 
                (category_id, account_id, amount)
                VALUES (?, ?, ?)""",
                (category_id, account_id, amount))

    async def delete_category(self, user_id, category_id):
        await self._cur.execute("""DELETE FROM transactions
            WHERE category_id = ?""",
            (category_id,))

        await self._cur.execute("""DELETE FROM categories 
                WHERE category_id = ?""",
                (category_id,))

    async def delete_account(self, user_id, account_id):
        await self._cur.execute("""DELETE FROM transactions
            WHERE account_id = ?""",
            (account_id,))

        await self._cur.execute("""DELETE FROM accounts 
                WHERE account_id = ?""",
                (account_id,))

    async def get_categories(self, user_id):
        await self._cur.execute("""SELECT categories.name FROM categories
                WHERE owner_id = ?""",
                (user_id,))

        categories = []
        result = await self._cur.fetchall()
        for row in result:
            categories.append(row[0])
        return categories

    async def get_accounts(self, user_id):
        await self._cur.execute("""SELECT accounts.name FROM accounts
                WHERE owner_id = ?""",
                (user_id,))

        accounts = []
        result = await self._cur.fetchall()
        for row in result:
            accounts.append(row[0])
        return accounts





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
                user_id = message.from_user.id
                result = await data.exists_user(user_id)

                if not result:
                    result = await data.add_user(user_id)

                tg.create_task(message.reply(messages.START))
                tg.create_task(con.commit())

            @dp.message_handler(commands=["recreate", "кускуфеу"])
            async def recreate_message(message: types.Message):
                if message.from_user.id == config.ADMIN_ID:
                    await data.delete()
                    await data.create()

                    tg.create_task(bot.send_message(message.from_user.id, messages.RECREATE_DONE,
                            reply_markup=ReplyKeyboardRemove()))
                    tg.create_task(con.commit())


            @dp.message_handler(commands=["help", "рудз"])
            async def help_message(message: types.Message):
                await message.reply(messages.HELP, parse_mode=types.ParseMode.HTML)

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
                        exists = await data.exists_category(user_id, name)

                        if exists:
                            tg.create_task(message.reply(
                                    messages.DOUBLE_CATEGORY_ADD.format(name=name),
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            await data.add_category(user_id, name)
                            tg.create_task(message.reply(
                                    messages.SUCCESSFUL_CATEGORY_ADD.format(name=name),
                                    parse_mode=types.ParseMode.HTML))

                    case "добавить"|"доб", "счет"|"счёт", name:
                        exists = await data.exists_account(user_id, name)

                        if exists:
                            tg.create_task(message.reply(
                                    messages.DOUBLE_ACCOUNT_ADD.format(name=name),
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            result = await data.add_account(user_id, name)
                            tg.create_task(message.reply(
                                    messages.SUCCESSFUL_ACCOUNT_ADD.format(name=name),
                                    parse_mode=types.ParseMode.HTML))

                    case "удалить"|"уд", "категорию"|"кат", name:
                        category_id = await data.get_category_id(user_id, name)

                        if category_id == -1:
                            tg.create_task(message.reply(
                                    messages.CATEGORY_NOT_EXIST.format(name=name),
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            await data.delete_category(user_id, category_id)
                            tg.create_task(message.reply(
                                    messages.SUCCESSFUL_CATEGORY_DELETE.format(name=name),
                                    parse_mode=types.ParseMode.HTML))

                    case "удалить"|"уд", "счет"|"счёт", name:
                        account_id = await data.get_account_id(user_id, name)

                        if account_id == -1:
                            tg.create_task(message.reply(
                                    messages.ACCOUNT_NOT_EXIST.format(name=name),
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            await data.delete_account(user_id, account_id)
                            tg.create_task(message.reply(
                                    messages.SUCCESSFUL_ACCOUNT_DELETE.format(name=name),
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

                    case "категории",:
                        categories = await data.get_categories(user_id)

                        if not categories:
                            tg.create_task(message.reply(messages.NO_CATEGORIES,
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            tg.create_task(message.reply(
                                    messages.CATEGORIES.format(
                                        categories=messages.CATEGORIES_SEP.join(categories)),
                                    parse_mode=types.ParseMode.HTML))

                    case "счета",:
                        accounts = await data.get_accounts(user_id)

                        if not accounts:
                            tg.create_task(message.reply(messages.NO_ACCOUNTS,
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            tg.create_task(message.reply(
                                    messages.ACCOUNTS.format(
                                        accounts=messages.ACCOUNTS_SEP.join(accounts)),
                                    parse_mode=types.ParseMode.HTML))

                    case _:
                        tg.create_task(message.reply(messages.UNKNOWN_COMMAND))

                tg.create_task(con.commit())


            executor.start_polling(dp, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())

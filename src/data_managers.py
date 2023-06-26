from datetime import datetime

import aiosqlite as sq


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
            amount INTEGER NOT NULL,
            day DATE NOT NULL
            )""")

    async def delete(self):
        await self._cur.execute("""DROP TABLE IF EXISTS users""")
        await self._cur.execute("""DROP TABLE IF EXISTS accounts""")
        await self._cur.execute("""DROP TABLE IF EXISTS categories""")
        await self._cur.execute("""DROP TABLE IF EXISTS transactions""")

    async def get_balance(self, user_id, account_name=None):
        if account_name is not None:
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
                (category_id, account_id, amount, day)
                VALUES (?, ?, ?, ?)""",
                (category_id, account_id, amount, datetime.today().strftime('%Y-%m-%d')))

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

    async def get_transactions_by_time(self, user_id, begin, end, category_id=None):
        if category_id is None:
            await self._cur.execute("""SELECT amount, day FROM transactions
                    JOIN accounts ON transactions.account_id = accounts.account_id
                    WHERE owner_id = ? AND day BETWEEN ? AND ?""",
                    (user_id, begin, end))
        else:
            await self._cur.execute("""SELECT amount, day FROM transactions
                    JOIN accounts ON transactions.account_id = accounts.account_id
                    WHERE (owner_id, category_id) = (?, ?) AND day BETWEEN ? AND ?""",
                    (user_id, category_id, begin, end))

        result = await self._cur.fetchall()
        return [] if result is None else [list(row) for row in result];

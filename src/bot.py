from datetime import datetime
import time
import random

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import KeyboardButton
import matplotlib.pyplot as plt
import seaborn as sns

import src.config as config
import src.messages as messages

def isfloat(number):
    try:
        float(number)
        return True
    except ValueError:
        return False

def is_date_correct(date):
    try:
        datetime.strptime(date, "%Y-%m-%d") 
    except ValueError:
        return False
    return True

def compress_transactions(transactions):
    if not transactions:
        return transactions
    compressed_transactions = [transactions[0]]
    for i in range(1, len(transactions)):
        if transactions[i][1] == compressed_transactions[-1][1]:
            compressed_transactions[-1][0] += transactions[i][0]
        else:
            compressed_transactions.append(transactions[i])
    return compressed_transactions


def make_plot(transactions, category_name=None):
    transactions = compress_transactions(transactions)
    dates = [data[1] for data in transactions]
    amounts = [data[0] for data in transactions]
    ax = sns.stripplot(x=dates, y=amounts);
    ax = sns.lineplot(x=dates, y=amounts)
    ax.set(xlabel = "День", ylabel = "Сумма")
    plt.title("Статистика по всем категориям" if category_name is None else 
            f"Статистика по категории {category_name}")
    figure = plt.gcf()
    file_name = str(time.time() * random.randint(1, 100)).replace('.', '')
    file_path = f"{file_name}.png"
    figure.savefig(f"{file_name}.png", dpi=300)
    plt.clf()
    return file_path


class MessageHandler:
    _tg = None
    _data = None
    _con = None

    async def init(self, tg, data, con):
        self._tg = tg
        self._data = data
        self._con = con

    async def add_category_message(self, message, name):
        user_id = message.from_user.id
        exists = await self._data.exists_category(user_id, name)

        if exists:
            self._tg.create_task(message.reply(
                    messages.DOUBLE_CATEGORY_ADD.format(name=name),
                    parse_mode=types.ParseMode.HTML))
        else:
            await self._data.add_category(user_id, name)
            self._tg.create_task(message.reply(
                    messages.SUCCESSFUL_CATEGORY_ADD.format(name=name),
                    parse_mode=types.ParseMode.HTML))

    async def add_account_message(self, message, name):
        user_id = message.from_user.id
        exists = await self._data.exists_account(user_id, name)

        if exists:
            self._tg.create_task(message.reply(
                    messages.DOUBLE_ACCOUNT_ADD.format(name=name),
                    parse_mode=types.ParseMode.HTML))
        else:
            await self._data.add_account(user_id, name)
            self._tg.create_task(message.reply(
                    messages.SUCCESSFUL_ACCOUNT_ADD.format(name=name),
                    parse_mode=types.ParseMode.HTML))

    async def delete_category_message(self, message, name):
        user_id = message.from_user.id
        category_id = await self._data.get_category_id(user_id, name)

        if category_id == -1:
            self._tg.create_task(message.reply(
                    messages.CATEGORY_NOT_EXIST.format(name=name),
                    parse_mode=types.ParseMode.HTML))
        else:
            await self._data.delete_category(user_id, category_id)
            self._tg.create_task(message.reply(
                    messages.SUCCESSFUL_CATEGORY_DELETE.format(name=name),
                    parse_mode=types.ParseMode.HTML))

    async def delete_account_message(self, message, name):
        user_id = message.from_user.id
        account_id = await self._data.get_account_id(user_id, name)

        if account_id == -1:
            self._tg.create_task(message.reply(
                    messages.ACCOUNT_NOT_EXIST.format(name=name),
                    parse_mode=types.ParseMode.HTML))
        else:
            await self._data.delete_account(user_id, account_id)
            self._tg.create_task(message.reply(
                    messages.SUCCESSFUL_ACCOUNT_DELETE.format(name=name),
                    parse_mode=types.ParseMode.HTML))

    async def add_transaction_message(self, message, amount, category, account):
        user_id = message.from_user.id
        category_id = await self._data.get_category_id(user_id, category)
        account_id = await self._data.get_account_id(user_id, account)

        match category_id, account_id:
            case -1, -1:
                self._tg.create_task(message.reply(
                        messages.CATEGORY_AND_ACCOUNT_NOT_EXIST.format(
                        category=category, account=account),
                        parse_mode=types.ParseMode.HTML))
            case -1, _:
                self._tg.create_task(message.reply(
                        messages.CATEGORY_NOT_EXIST.format(name=category),
                        parse_mode=types.ParseMode.HTML))
            case _, -1:
                self._tg.create_task(message.reply(
                        messages.ACCOUNT_NOT_EXIST.format(name=account),
                        parse_mode=types.ParseMode.HTML))
            case _, _:
                await self._data.add_transaction(user_id, 
                        float(amount.replace(',', '.')), category_id, account_id)
                self._tg.create_task(message.reply(
                        messages.TRANSACTION_ADD.format(amount=amount, 
                            category=category, account=account),
                        parse_mode=types.ParseMode.HTML))

    async def get_balance_message(self, message, account=None):
        user_id = message.from_user.id
        if account is not None:
            exists = await self._data.exists_account(user_id, account)

        if account is not None and not exists:
            self._tg.create_task(message.reply(
                    messages.ACCOUNT_NOT_EXIST.format(name=account),
                    parse_mode=types.ParseMode.HTML))
        else:
            balance = await self._data.get_balance(user_id, account)
            if account is not None:
                self._tg.create_task(message.reply(
                        messages.ACCOUNT_BALANCE.format(balance=round(balance, 2),
                            account=account), 
                        parse_mode=types.ParseMode.HTML))
            else:
                self._tg.create_task(message.reply(
                        messages.BALANCE.format(balance=round(balance, 2)),
                        parse_mode=types.ParseMode.HTML))

    async def get_statistics_message(self, message, begin, end, category=None):
        user_id = message.from_user.id
        if category is not None:
            category_id = await self._data.get_category_id(user_id, category)

        if category is not None and category_id == -1:
            self._tg.create_task(message.reply(
                    messages.CATEGORY_NOT_EXIST.format(name=category),
                    parse_mode=types.ParseMode.HTML))
        elif not is_date_correct(begin):
            self._tg.create_task(message.reply(
                    messages.DATE_INCORRECT.format(date=begin),
                    parse_mode=types.ParseMode.HTML))
        elif not is_date_correct(end):
            self._tg.create_task(message.reply(
                    messages.DATE_INCORRECT.format(date=end),
                    parse_mode=types.ParseMode.HTML))
        elif begin > end:
            self._tg.create_task(message.reply(messages.DATE_ORDER_INCORRECT,
                    parse_mode=types.ParseMode.HTML))
        else:
            result = await self._data.get_transactions_by_time(user_id, begin, end, category)
            amount = round(sum(data[0] for data in result), 2)
            file_name = make_plot(result, category)
            photo = open(file_name, "rb")

            if category is not None:
                self._tg.create_task(message.answer_photo(photo, caption=
                        messages.TIME_STATISTICS_CATEGORY.format(begin=begin,
                            end=end, amount=amount, category=category),
                        parse_mode=types.ParseMode.HTML))
            else:
                self._tg.create_task(message.answer_photo(photo, caption=
                    messages.TIME_STATISTICS.format(begin=begin,
                        end=end, amount=amount),
                    parse_mode=types.ParseMode.HTML))

    async def get_categories_message(self, message):
        user_id = message.from_user.id
        categories = await self._data.get_categories(user_id)

        if not categories:
            self._tg.create_task(message.reply(messages.NO_CATEGORIES,
                    parse_mode=types.ParseMode.HTML))
        else:
            self._tg.create_task(message.reply(
                    messages.CATEGORIES.format(
                        categories=messages.CATEGORIES_SEP.join(categories)),
                    parse_mode=types.ParseMode.HTML))

    async def get_accounts_message(self, message):
        user_id = message.from_user.id
        accounts = await self._data.get_accounts(user_id)

        if not accounts:
            self._tg.create_task(message.reply(messages.NO_ACCOUNTS,
                    parse_mode=types.ParseMode.HTML))
        else:
            self._tg.create_task(message.reply(
                    messages.ACCOUNTS.format(
                        accounts=messages.ACCOUNTS_SEP.join(accounts)),
                    parse_mode=types.ParseMode.HTML))

    async def unknown_command_message(self, message):
        self._tg.create_task(message.reply(messages.UNKNOWN_COMMAND))

    async def start_message(self, message):
        user_id = message.from_user.id
        result = await self._data.exists_user(user_id)

        if not result:
            result = await self._data.add_user(user_id)

        self._tg.create_task(message.reply(messages.START))
        self._tg.create_task(self._con.commit())

    async def recreate_message(self, message):
        if message.from_user.id == config.ADMIN_ID:
            await self._data.delete()
            await self._data.create()

            self._tg.create_task(message.reply(messages.RECREATE_DONE,
                    reply_markup=ReplyKeyboardRemove()))
            self._tg.create_task(self._con.commit())

    async def help_message(self, message):
        await message.reply(messages.HELP, parse_mode=types.ParseMode.HTML)

    async def reply_message(self, message):
        user_id = message.from_user.id
        result = await self._data.exists_user(user_id)
        if not result:
            await message.reply(messages.REGISTER_REQUIRED)
            return

        tokens = [word.lower() for word in message.text.split()]

        match tokens:
            case "добавить"|"доб", "категорию"|"кат", name:
                await self.add_category_message(message, name)

            case "добавить"|"доб", "счет"|"счёт", name:
                await self.add_account_message(message, name)

            case "удалить"|"уд", "категорию"|"кат", name:
                await self.delete_category_message(message, name)

            case "удалить"|"уд", "счет"|"счёт", name:
                await self.delete_account_message(message, name)

            case amount, category, account if isfloat(amount.replace(',', '.')):
                await self.add_transaction_message(message, amount, category, account)

            case "баланс"|"бал", account:
                await self.get_balance_message(message, account)

            case "баланс"|"бал",:
                await self.get_balance_message(message)

            case "статистика"|"стата", begin, end, category:
                await self.get_statistics_message(message, begin, end, category)

            case "статистика"|"стата", begin, end:
                await self.get_statistics_message(message, begin, end)

            case "категории",:
                await self.get_categories_message(message)

            case "счета",:
                await self.get_accounts_message(message)

            case _:
                await self.unknown_command_message(message)

        self._tg.create_task(self._con.commit())

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

import config
import messages
from data_managers import UsersData

nest_asyncio.apply()


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

                    case "статистика"|"стата", begin, end, category:
                        category_id = await data.get_category_id(user_id, category)

                        if category_id == -1:
                            tg.create_task(message.reply(
                                    messages.CATEGORY_NOT_EXIST.format(name=category),
                                    parse_mode=types.ParseMode.HTML))
                        elif not is_date_correct(begin):
                            tg.create_task(message.reply(
                                    messages.DATE_INCORRECT.format(date=begin),
                                    parse_mode=types.ParseMode.HTML))
                        elif not is_date_correct(end):
                            tg.create_task(message.reply(
                                    messages.DATE_INCORRECT.format(date=end),
                                    parse_mode=types.ParseMode.HTML))
                        elif begin > end:
                            tg.create_task(message.reply(messages.DATE_ORDER_INCORRECT,
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            result = await data.get_transactions_by_time(user_id, begin, 
                                    end, category_id)
                            tg.create_task(message.reply(
                                    messages.TIME_STATISTICS_CATEGORY.format(begin=begin,
                                        end=end, amount=result, category=category),
                                    parse_mode=types.ParseMode.HTML))

                    case "статистика"|"стата", begin, end:
                        if not is_date_correct(begin):
                            tg.create_task(message.reply(
                                    messages.DATE_INCORRECT.format(date=begin),
                                    parse_mode=types.ParseMode.HTML))
                        elif not is_date_correct(end):
                            tg.create_task(message.reply(
                                    messages.DATE_INCORRECT.format(date=end),
                                    parse_mode=types.ParseMode.HTML))
                        elif begin > end:
                            tg.create_task(message.reply(messages.DATE_ORDER_INCORRECT,
                                    parse_mode=types.ParseMode.HTML))
                        else:
                            result = await data.get_transactions_by_time(user_id, begin, end)
                            tg.create_task(message.reply(
                                    messages.TIME_STATISTICS.format(begin=begin,
                                        end=end, amount=result),
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

START = """Привет! С помощью этого бота ты можешь удобно следить за своими финансами😉
Рекомендую начать с команды /help"""

TRANSACTION_ADD = """Операция на <code>{amount}</code> категории <code>{category}</code> успешно добавлена на счет <code>{account}</code>🤙"""
SUCCESSFUL_CATEGORY_ADD = """Категория <code>{name}</code> успешно создана😎"""
SUCCESSFUL_ACCOUNT_ADD = """Счет <code>{name}</code> успешно создан😎"""

SUCCESSFUL_CATEGORY_DELETE = """Категория <code>{name}</code> успешно уничтожена🤯"""
SUCCESSFUL_ACCOUNT_DELETE = """Счет <code>{name}</code> успешно уничтожен🤯"""

DOUBLE_CATEGORY_ADD = """Категория <code>{name}</code> уже существует😼"""
DOUBLE_ACCOUNT_ADD = """Счет <code>{name}</code> уже существует😼"""

CATEGORY_NOT_EXIST = """Категории <code>{name}</code> не существует😩"""
ACCOUNT_NOT_EXIST = """Счета <code>{name}</code> не существует😩"""
CATEGORY_AND_ACCOUNT_NOT_EXIST = """Ни категории <code>{category}</code>, ни счета <code>{account}</code> не существует😫"""

RECREATE_DONE = """Таблица успешно пересоздана, все данные были удалены!🤯"""

BALANCE = """Твой текущий баланс: <code>{balance} {currency}</code>🤑"""
ACCOUNT_BALANCE = """Твой текущий баланс на счете <code>{account}</code>: <code>{balance} {currency}</code>🤑"""

CURRENCY_CONVERSION_ERROR = """К сожалению, не получилось найти валюты <code>{currency}</code>😭
Список доступных валют можно найти на этом сайте: https://www.cbr-xml-daily.ru"""

CATEGORIES = """Вот все твои категории😛
<code>{categories}</code>"""
NO_CATEGORIES = """У тебя нет ни одной категории😔"""
CATEGORIES_SEP = """</code>\n<code>"""

ACCOUNTS = """Вот все твои счета😛
<code>{accounts}</code>"""
NO_ACCOUNTS = """У тебя нет ни одного счета😔"""
ACCOUNTS_SEP = """</code>\n<code>"""

TIME_STATISTICS_CATEGORY = """В промежуток между днем <code>{begin}</code> и <code>{end}</code> твой баланс изменился на <code>{amount} {currency}</code> по категории <code>{category}</code>🥳
На графике можно увидеть все подробности👀"""
TIME_STATISTICS = """В промежуток между днем <code>{begin}</code> и <code>{end}</code> твой баланс изменился на <code>{amount} {currency}</code>🥳
На графике можно увидеть все подробности👀"""

DATE_INCORRECT = """День <code>{date}</code> записан некорректно😵
Он должен быть корректным днем, записанным в формате <code>YYYY-MM-DD</code>🧐"""
DATE_ORDER_INCORRECT = """Первый день должен быть раньше второго😬"""

HELP = """Вот команды, которые можно использовать
Сами команды написаны на русском и их можно сокращать (например, "доб" вместо "добавить")
На английском написаны аргументы, в квадратных скобках необязательные.

<code>добавить категорию name</code> - добавляет новую категорию расходов/доходов с названием <code>name</code>

<code>удалить категорию name</code> - удаляет категорию с названием <code>name</code> а также все операции, которые были с ней произведены

<code>категории</code> - увидеть список всех своих категорий

<code>добавить счет name</code> - добавляет новый счет с названием <code>name</code>

<code>удалить счет name</code> - удаляет счет с названием <code>name</code> а также все операции, которые были с ним связаны

<code>счета</code> - увидеть список всех своих счетов

<code>amount category account</code> - добавляет операцию суммой <code>amount</code> категории <code>category</code> на счет <code>account</code>

<code>баланс [account] [currency]</code> - выводит суммарный баланс пользователя, или же только по счету <code>account</code>, если он указан. Если <code>currency</code> указан вторым аргументом, то выводит баланс, переведенный на указанную валюту

<code>статистика begin end [category] [currency]</code> - выводит суммарные траты по дням между <code>begin</code> и <code>end</code> по всем категориям, или же только по <code>category</code>, если указана. Если <code>currency</code> указан четвертым аргументом, то выводит статистику, переведенную на указанную валюту
"""

REGISTER_REQUIRED = """Сначала тебе необходимо написать /start!🤬"""

UNKNOWN_COMMAND = """К сожалению, я не понял, что ты имеешь в виду🙄
На всякий случай: советую написать /help"""
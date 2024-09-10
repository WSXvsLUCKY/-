import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

#-----------------------------------------------------------
API_TOKEN = '7283669108:AAHPESJSQivUrxx_Wtnkh9rtLvYJxAzR2Hg'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
#-----------------------------------------------------------
# база данных
conn = sqlite3.connect('finance_bot.db')
cursor = conn.cursor()

# Создание таблиц
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    category TEXT,
    date TEXT,
    type TEXT
)
''')
conn.commit()

def add_user(user_id, username=None):
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username)
    VALUES (?, ?)
    ''', (user_id, username))
    conn.commit()

def add_transaction(user_id, amount, category, date, type):
    add_user(user_id)
    cursor.execute('''
    INSERT INTO transactions (user_id, amount, category, date, type)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, amount, category, date, type))
    conn.commit()

def get_balance(user_id):
    cursor.execute('''
    SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'income'
    ''', (user_id,))
    income = cursor.fetchone()[0] or 0

    cursor.execute('''
    SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense'
    ''', (user_id,))
    expenses = cursor.fetchone()[0] or 0

    return income - expenses

def filter_transactions(user_id, category=None, start_date=None, end_date=None):
    query = 'SELECT * FROM transactions WHERE user_id = ?'
    params = [user_id]

    if category:
        query += ' AND category = ?'
        params.append(category)

    if start_date and end_date:
        query += ' AND date BETWEEN ? AND ?'
        params.append(start_date)
        params.append(end_date)

    cursor.execute(query, params)
    return cursor.fetchall()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username)
    await message.answer("Привет! Я помогу тебе управлять финансами.\n"
                         "Для начала, используй /help для списка команд.")

@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.answer("/balance - Посмотреть баланс\n"
                         "/add_income - Добавить доход\n"
                         "/add_expense - Добавить расход\n"
                         "/history - История транзакций")

@dp.message_handler(commands=['balance'])
async def balance(message: types.Message):
    user_id = message.from_user.id
    balance = get_balance(user_id)
    await message.answer(f'Текущий баланс: {balance} руб.')

@dp.message_handler(commands=['add_income'])
async def add_income(message: types.Message):
    await message.answer("Введите доход в формате: доход <сумма> <категория> <дата (YYYY-MM-DD)>")

@dp.message_handler(lambda message: message.text.startswith('доход'))
async def handle_income(message: types.Message):
    try:
        user_id = message.from_user.id
        _, amount, category, date = message.text.split()
        add_transaction(user_id, float(amount), category, date, 'income')
        await message.answer(f'Доход {amount} руб. добавлен в категорию "{category}" на дату {date}.')
    except:
        await message.answer("Неверный формат данных. Введите в формате: доход <сумма> <категория> <дата (YYYY-MM-DD)>")

@dp.message_handler(commands=['add_expense'])
async def add_expense(message: types.Message):
    await message.answer("Введите расход в формате: расход <сумма> <категория> <дата (YYYY-MM-DD)>")

@dp.message_handler(lambda message: message.text.startswith('расход'))
async def handle_expense(message: types.Message):
    try:
        user_id = message.from_user.id
        _, amount, category, date = message.text.split()
        add_transaction(user_id, float(amount), category, date, 'expense')
        await message.answer(f'Расход {amount} руб. добавлен в категорию "{category}" на дату {date}.')
    except:
        await message.answer("Неверный формат данных. Введите в формате: расход <сумма> <категория> <дата (YYYY-MM-DD)>")

@dp.message_handler(commands=['history'])
async def history(message: types.Message):
    user_id = message.from_user.id
    transactions = filter_transactions(user_id)

    if transactions:
        history_text = "История транзакций:\n\n"
        for t in transactions:
            history_text += f"{t[3]} | {t[2]} руб. | Категория: {t[4]} | Тип: {t[5]}\n"
        await message.answer(history_text)
    else:
        await message.answer("У вас пока нет транзакций.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

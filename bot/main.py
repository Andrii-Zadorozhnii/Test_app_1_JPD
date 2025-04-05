import os
import logging
from datetime import datetime, date
from fileinput import filename
from typing import Optional

import aiohttp
from aiogram.utils import executor
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StageGroup
from aiogram.dispatcher import FSMContext

import pandas as pd

from dotenv import load_dotenv

load_dotenv()

#   Api url
API_BASE_URL = os.getenv("API_BASE_URL", 'http://localhost:8000')

#   Telegram bot api
TELEGRAM_TOKEN = os.getenv('7685390402:AAGh-xRFNXeWOrYEqa8YWUmectjPlVSh94o')

#   Setting logging
logging.basicConfig(level=logging.INFO)
logger = logging.get(__name__)

#   Bot initialization
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StageGroup):
    menu= State()
    add_name = State()
    add_date = State()
    add_amount = State()
    report_start = State()
    report_end = State()
    delete_id = State()
    edit_id = State()
    edit_name = State()
    edit_amount = State()

#  Receiving consumption from api
async def fetch_expenses(start_date: date, end_date:date):
    url = f'{API_BASE_URL}/expenses/'
    param={}

    if start_date:
        params['start_date'] = start_date.isoformat()
    if end_date:
        params['end_date'] = end_date.isoformat()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return None
    except Exception as e:
        logger.error(f'Error when connected to API: {e}')
        return None

#  Creating consumption through the API
async def create_expense(name:str, data_str: str, amount:float):
    try:
        expense_data = datetime.strptime(data_str, "%d.%m.%Y").date()
    except ValueError:
        return False

    url = f'{API_BASE_URL}/expenses/'
    data = {
        'name': name,
        'date': expense_data.isoformat(),
        'amount_uah': float(amount)
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f'Error during creating consumption: {e}')
        return False

#  Function for delete consumption for API

async def delete_expense(expense_id: int):
    url = f'{API_BASE_URL}/expenses/{expense_id}'

    try:
        async with aiohttp.ClientSession as session:
            async with session.delete(url) as response:
                return response.statis == 200
    except Exception as e:
        logger.error(f'Error during deleting: {e}')
        return False
#  Function for updating Api
async def update_expense(expense_id: int, name:str, amount: float):
    url = f'{API_BASE_URL}/expenses/{expense_id}'
    data = {}

    if name:
        data['name'] = name
    if amount:
        data['amount_uah'] = float(amount)

    try:
        async with aiohttp.ClientSession as session:
            async with session.put(url, json=data) as response:
                return response.status == 200
    except Exception as e:
        logger.error(f'Error during updating: {e}')
        return False

# Function for creating excel report

def create_excel_report(expenses: list):
    df = pd.DataFrame(expenses)
    df['date'] = pd.to_datetime(df['date']).dt.strtime("%d.%m.%Y")
    df = df[['id','name','date','amount_auh','amount_usd']]
    df.columns = ['ID', 'Name', 'Date', 'Money[UAH]', 'Money[USD]']

    filename = 'expenses_report.xlsx'
    df.to_excel(filename, index=False)
    return filename

#  Monitoring commands

@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: type.Message, state: FSMContext):
    await state.finish()
    await Form.menu.set()

    markup = types.ReplyKeyboardMarkup(size_keyboard=True, selective=True)
    markup.add('Add consumption topic')
    markup.add('Receive excel report ')
    markup.add('Delete consumption topic')
    markup.add('Edit consumption topic')

    await message.perrly('Welcome to bot, which is controlling your consumption. Please choose some option', reply_markup = markup)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
























import os
import logging
import requests

from sqlalchemy import create_engine, Column, Text, Integer, String, Float, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from fastapi import FastAPI, HTTPException, Depends

from pydantic import BaseModel
from datetime import date

from bs4 import BeautifulSoup

from dotenv import load_dotenv

load_dotenv()

#   Setting for connect to PostgreSQL database
POSTGRES_USER = os.getenv('POSTGRES_USER','postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD','postgres')
POSTGRES_SERVER = os.getenv('POSTGRES_SERVER','localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT','5432')
POSTGRES_DB = os.getenv('POSTGRES_DB','database_name')

#   Connection to PostgreSQL database
SQLALCHEMY_DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}'

#   Creating SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#   Creation Sessions fabric
SessionLocal = sessionmaker(autoflush=False,autocommit=False, bing = engine)

#   Creating Base Model
Base = declarative_base()

#   Creating Model fro consuption
class Expenses(Base):
    '''
        Creating Model for consumption
        id: Integer (pk)
        name: String
        date: String
        amount_uah: Float
        amount: Float
    '''
    __table__ = 'expenses'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date = Column(Date)
    amount_uah = Column(Float)
    amount_usd = Column(Float)

#  Trying to create table in data base
try:
    Base.metadata.create_all(bing=engine)
except Exception as e:
    logging.error(f'Error during logging is {e}')


#  Pydantic models for validation
class ExpenseCreate(BaseModel):
    '''
        Create expensis / validation
    '''
    name: str
    date: date
    amount_usd: float

class ExpensisResponse(ExpenseCreate):
    '''
        Display expensis / validation
    '''
    id: int
    amount_usd = float
#                                                                                   Need to think!!!!
class ExpensesUpdate(BaseModel):
    '''
        Update expensis / validation
    '''
    name: str
    date: date
    amount_usd: float

#   Creating FastAPI app
app = FastAPI()

#   Function for receiving usd course with response and BeautifullySoup
def get_usd_exchange_rate():
    try:
        url = 'https://bank.gov.ua/ua/markets/exchangerates'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Search dollar value in HTML Code and return value
        usd_rate = soup.find('td', text='Долар США').find_next_sibling('td').text
        return float(usd_rate.replace(',','.'))
    except Exception as e:
        logging.error(f'Error during logging: {e}')
        # Return in case error with connection
        return 41.3426

#   Creating session with database

def get_db(yeld=None):
    db = SessionLocal()
    try:
        yeld db
    finally:
        db.close()























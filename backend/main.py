import os
import logging
import requests

from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from fastapi import FastAPI, HTTPException, Depends

from pydantic import BaseModel
from datetime import date

from bs4 import BeautifulSoup
from typing import List
from dotenv import load_dotenv

load_dotenv()

#   Setting for connect to PostgreSQL database
POSTGRES_USER = os.getenv('POSTGRES_USER','postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD','0711')
POSTGRES_SERVER = os.getenv('POSTGRES_SERVER','localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT','5432')
POSTGRES_DB = os.getenv('POSTGRES_DB','Test_app_1_JPD')

#   Connection to PostgreSQL database
SQLALCHEMY_DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}'

#   Creating SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#   Creation Sessions fabric
SessionLocal = sessionmaker(autoflush=False,autocommit=False, bind = engine)

#   Creating Base Model
Base = declarative_base()

#   Creating Model fro consuption
class Expense(Base):
    '''
        Creating Model for consumption
        id: Integer (pk)
        name: String
        date: String
        amount_uah: Float
        amount: Float
    '''
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date = Column(Date)
    amount_uah = Column(Float)
    amount_usd = Column(Float)

#  Trying to create table in database
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.error(f'Error during logging is {e}')


#  Pydantic models for validation
class ExpenseCreate(BaseModel):
    '''
        Create expensis / validation
    '''
    name: str
    date: date
    amount_uah: float

class ExpenseResponse(ExpenseCreate):
    '''
        Display expensis / validation
    '''
    id: int
    amount_usd: float
#                                                                      Need to think!!!!
class ExpenseUpdate(BaseModel):
    '''
        Update expensis / validation
    '''
    name: str
    date: date
    amount_uah: float

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#   Endpoint for creating consumption

@app.post('/expenses/', response_model=ExpenseResponse)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    usd_rate = get_usd_exchange_rate()
    amount_usd = expense.amount_uah / usd_rate

    db_expense = Expense(
        name=expense.name,
        date=expense.date,
        amount_uah=expense.amount_uah,
        amount_usd = amount_usd
    )

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return db_expense

#  Endpoint for receiving consumption

@app.get('/expenses/', response_model=List[ExpenseResponse])
def read_expense(start_date: date = None, end_date:date = None, db:Session = Depends(get_db)):
    query = db.query(Expense)

    #   Filter by dates
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    return query.order_by(Expense.date).all()


#   Endpoint for deleting consumption
@app.delete('/expenses/{expense_id}')
def delete_expense(expense_id: int, db: Session = Depends(get_db)):

    expense = db.query(Expense).filter(Expense.id == expense_id).first()

    if not expense:
        raise HTTPException(status_code=404, detail="No expense")

    db.delete(expense)
    db.commit()

    return{'message': 'Positive delite'}

#   Endpoint for update consumprion
@app.put('/expenses/{expense_id}')
def update_expense(expenses_id: int, expenses_update: ExpenseUpdate, db: Session = Depends(get_db)):

    db_expense = db.query(Expense).filter(Expense.id == expenses_id).first()

    if not db_expense:
        raise HTTPException(status_code=404, detail="No expense")

    # Update
    if expenses_update.name is not None:
        db_expense.name = expenses_update.name
    if expenses_update.date is not None:
        db_expense.date = expenses_update.date
    if expenses_update.amount_uah is not None:
        usd_rate = get_usd_exchange_rate()
        db_expense.amount_uah = expenses_update.amount_uah
        db_expense.amount_usd = expenses_update.amount_uah / usd_rate

    db.commit()
    db.refresh(db_expense)

    return db_expense


















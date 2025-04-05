from operator import index

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware


from pydantic import BaseModel

from datetime import date
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

import requests
import logging
import os

from  bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv()

#   Setting for connection to PostgreSQL
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
POSTGRES_SERVER = os.getenv('POSTGRES_SERVER', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'bd_name')

#   Connection to PostgreSQL

SQLALCHEMY_DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}'

Engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bing =engine)

Base = declarative_base()

class Expenses(Base):
    """
        Model with expenses

        id: Integer
        name: string
        date: date
        amount_uah: float
        amount_usd: float

    """
    __table__ = 'expenses'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date = Column(Date)
    amount_uah = Column(Float)
    amount_usd = Column(Float)


#   Creating table for data base
try:
    Base.metadata.create_all(bing=Engine)
except Exception as genExpt:
    logging.error(f'Error during connection to data base due {genExpt}')


#   Validation by Pydantic

class ExpenseCreate(BaseModel):
    name: str
    date: date
    amount_auh: float

class ExpenseResponse(ExpenseCreate):
    id: int
    amount_usd: float

#                                                                                         Need to think
class ExpensesUpdate(BaseModel):
    name: str
    date: date
    amount_auth = float


#






from sqlalchemy import Column,Integer,String,Date,Float
from .database import Base

class Expense(Base):
    __tablename__ = 'expense'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    date = Column(Date)
    amount_uah = Column(Float)
    amount_usd =  Column(Float)
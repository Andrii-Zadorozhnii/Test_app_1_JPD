# backend/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import requests
from bs4 import BeautifulSoup
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "expense_tracker")

# Database connection URL
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Expense model
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    date = Column(Date)
    amount_uah = Column(Float)
    amount_usd = Column(Float)


# Create tables
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logging.error(f"Error creating tables: {e}")


# Pydantic models
class ExpenseCreate(BaseModel):
    name: str
    date: date
    amount_uah: float


class ExpenseResponse(ExpenseCreate):
    id: int
    amount_usd: float


class ExpenseUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    amount_uah: Optional[float] = None


# FastAPI app
app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Get USD exchange rate
def get_usd_exchange_rate() -> float:
    try:
        url = "https://api.privatbank.ua/p24api/pubinfo?exchange&json&coursid=11"
        response = requests.get(url)
        data = response.json()
        usd_rate = next(item for item in data if item["ccy"] == "USD")["buy"]
        return float(usd_rate)
    except Exception as e:
        logging.error(f"Error getting exchange rate: {e}")
        return 36.5  # Fallback rate


# API endpoints
@app.post("/expenses/", response_model=ExpenseResponse)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    usd_rate = get_usd_exchange_rate()
    amount_usd = expense.amount_uah / usd_rate

    db_expense = Expense(
        name=expense.name,
        date=expense.date,
        amount_uah=expense.amount_uah,
        amount_usd=amount_usd
    )

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    return db_expense


@app.get("/expenses/", response_model=List[ExpenseResponse])
def read_expenses(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        db: Session = Depends(get_db)
):
    query = db.query(Expense)

    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    return query.order_by(Expense.date).all()


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}


@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
        expense_id: int,
        expense_update: ExpenseUpdate,
        db: Session = Depends(get_db)
):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if expense_update.name is not None:
        db_expense.name = expense_update.name
    if expense_update.date is not None:
        db_expense.date = expense_update.date
    if expense_update.amount_uah is not None:
        usd_rate = get_usd_exchange_rate()
        db_expense.amount_uah = expense_update.amount_uah
        db_expense.amount_usd = expense_update.amount_uah / usd_rate

    db.commit()
    db.refresh(db_expense)
    return db_expense
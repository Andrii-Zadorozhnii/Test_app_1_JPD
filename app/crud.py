from sqlalchemy.orm import Session
from . import models, schemas
from .currency import get_usd_exchange_rate

def get_expenses(db: Session):
    return db.query(models.Expense).all()

def get_expenses_by_date(db: Session, from_date, to_date):
    return db.query(models.Expense).filter(
        models.Expense.date >= from_date,
        models.Expense.date <= to_date
    ).all()

def create_expense(db:Session, expense: schemas.ExpenseCreate):
    usd_rate = get_usd_exchange_rate()
    expense_usd= expense.amount_uah / usd_rate
    db_expense = models.Expense(
        title=expense.title,
        date=expense.date,
        amount_uah = expense.amount_uah,
        amount_usd=round(expense_usd,2)
    )

    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def delete_expense(db:Session, expense_id:int):
    expense = db.query(models.Expense).get(expense_id)
    if expense:
        db.delete(expense)
        db.commit()
    return expense

def update_expense(db:Session, expense_id:int, new_date: schemas.ExpenseUpdate):
    expense = db.query(models.Expense).get(expense_id)

    if expense:
        usd_rate = get_usd_exchange_rate()
        expense.title = new_date.title
        expense.date = new_date.date
        expense.amount_uah = new_date.amount_uah
        expense.amount_usd = round(new_date.amount_uah / usd_rate, 2)
        db.commit()
        db.refresh(expense)

    return expense














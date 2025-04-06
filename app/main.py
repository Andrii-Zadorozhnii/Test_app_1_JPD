from typing import List
from datetime import date

from fastapi import FastAPI, Depends, HTTPException

from sqlalchemy.orm import Session
from . import schemas, crud,models
from .database import SessionLocal, engine,Base


#   Creating tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fast api handlers
@app.get('/expenses/', response_model=List[schemas.ExpenseInDB])
def read_expenses(db: Session = Depends(get_db)):
    return crud.get_expenses(db)

@app.get('/expenses/by_date/', response_model=List[schemas.ExpenseInDB])
def read_expenses(from_date:date, to_date:date, db:Session = Depends(get_db)):
    return crud.get_expenses_by_date(db, from_date,to_date)

@app.post('/expenses/', response_model=schemas.ExpenseInDB)
def create_new_expense(expense: schemas.ExpenseCreate, db:Session = Depends(get_db)):
    return crud.create_expense(db,expense)

@app.delete('/expenses/{expense_id}')
def delete_expense(expense_id:int, db:Session = Depends(get_db)):
    delete = crud.delete_expense(db, expense_id)
    if not delete:
        raise HTTPException(status_code=404, detail='Not found expense id')
    return {'ok': True}

@app.put('/expenses/{expense_id}', response_model=schemas.ExpenseInDB)
def update_expense(expense_id: int, update: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    updated_expense = crud.update_expense(db,expense_id,update)
    if not updated_expense:
        raise HTTPException(status_code=404, detail='Not found expense id')
    return updated_expense


























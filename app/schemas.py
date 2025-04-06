
from pydantic import BaseModel, ConfigDict
from datetime import date

class ExpenseBase(BaseModel):
    title: str
    date:date
    amount_uah:float

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(ExpenseBase):
    pass

class ExpenseInDB(ExpenseBase):
    amount_usd: float
    model_config = ConfigDict(from_attributes=True)
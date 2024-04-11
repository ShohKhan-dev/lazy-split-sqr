from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from app.database import Base
from app.models import User, Group, Expense, ExpenseParticipant, GroupMembership
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session
from typing import List

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
# @app.get("/")
# async def read_root():
#     return {"message": "Hello, World"}

# Pydantic models for request and response

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

class GroupCreate(BaseModel):
    group_name: str
    created_by: int

class ExpenseCreate(BaseModel):
    group_id: int
    description: str
    amount: int
    created_by: int

# Routes
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/groups/")
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    db_group = Group(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.post("/expenses/")
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = Expense(**expense.dict())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/groups/")
def get_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()

@app.get("/expenses/")
def get_expenses(db: Session = Depends(get_db)):
    return db.query(Expense).all()
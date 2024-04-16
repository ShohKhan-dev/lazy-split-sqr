from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.database import Base
from app.models import User, Group, Expense, ExpenseParticipant, GroupMembership
from app.database import engine, SessionLocal
from sqlalchemy.orm import Session, joinedload
from typing import List
from passlib.context import CryptContext

# Create a password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    # Check if the username or email already exists
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password before storing it in the database
    # hashed_password = pwd_context.hash(user.password)

    db_user = User(username=user.username, email=user.email, password=user.password)
    
    # Add the user to the database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Return a response with the created user data
    return db_user

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()



@app.post("/groups/")
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    db_group = Group(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    user = db.query(User).filter(User.user_id == db_group.created_by).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    group_membership = GroupMembership(group_id=db_group.group_id, user_id=user.user_id, is_admin=True)
    db.add(group_membership)
    db.commit()
    db.refresh(group_membership)


    return db_group

@app.get("/groups/{group_id}")
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).options(joinedload(Group.groupmembers), joinedload(Group.groupexpenses)).filter(Group.group_id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@app.get("/groups/")
def get_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()


@app.post("/groups/{group_id}/add_member/{user_id}")
def add_group_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update total members of the group
    group.total_members += 1
    db.commit()

    group_membership = GroupMembership(group_id=group_id, user_id=user_id)
    db.add(group_membership)
    db.commit()
    db.refresh(group_membership)
    return group_membership


# Delete a member from the group
@app.delete("/groups/{group_id}/delete_member/{user_id}")
def delete_group_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group_membership = db.query(GroupMembership).filter(GroupMembership.group_id == group_id,
                                                         GroupMembership.user_id == user_id).first()
    if group_membership is None:
        raise HTTPException(status_code=404, detail="Group member not found")

    # Update total members of the group
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if group:
        group.total_members -= 1
        db.commit()

    db.delete(group_membership)
    db.commit()
    return {"message": "Group member deleted successfully"}


# Delete a group
@app.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    db.delete(group)
    db.commit()
    return {"message": "Group deleted successfully"}

@app.post("/expenses/")
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = Expense(**expense.dict())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)

    # Update total expense of the group
    group = db.query(Group).filter(Group.group_id == db_expense.group_id).first()
    if group:
        group.total_expenses += db_expense.amount
        db.commit()

    return db_expense

@app.get("/expenses/{expense_id}")
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.expense_id == expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.get("/expenses/")
def get_expenses(db: Session = Depends(get_db)):
    return db.query(Expense).all()


# Delete an expense
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.expense_id == expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Update total expense of the group
    group_id = expense.group_id
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if group:
        group.total_expenses -= expense.amount
        db.commit()

    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}
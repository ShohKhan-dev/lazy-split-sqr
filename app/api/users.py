from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.models import (
    User,
    Group,
    GroupMembership,
    ExpenseParticipant,
    Expense,
)
from app.database import get_db
from pydantic import BaseModel
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    email: str


@router.get("/")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.get("/username/{username}")
def get_user_by_username(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the username or email already exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash the password before storing it in the database
    # hashed_password = pwd_context.hash(user.password)

    db_user = User(**user.dict())

    # Add the user to the database
    db.add(db_user)
    db.commit()

    # Return a response with the created user data
    db.refresh(db_user)
    return db_user


@router.get("/{user_id}/groups")
def get_user_groups(user_id: int, db: Session = Depends(get_db)):
    if db.query(User).filter(User.user_id == user_id).first() is None:
        raise HTTPException(status_code=404, detail="User not found")

    groups = (
        db.query(Group)
        .join(Group.groupmembers)
        .filter(GroupMembership.user_id == user_id)
        .all()
    )
    return groups


@router.get("/{user_id}/expenses")
def get_user_expenses(user_id: int, db: Session = Depends(get_db)):
    if db.query(User).filter(User.user_id == user_id).first() is None:
        raise HTTPException(status_code=404, detail="User not found")

    expenses_with_details = []
    expense_participants = (
        db.query(ExpenseParticipant)
        .filter(ExpenseParticipant.user_id == user_id)
        .all()
    )

    for expense_participant in expense_participants:
        expense = (
            db.query(Expense)
            .filter(Expense.expense_id == expense_participant.expense_id)
            .first()
        )
        expense_details = {
            "expense_description": expense.description,
            "expense_amount": expense.amount,
        }
        expenses_with_details.append(
            {**expense_participant.__dict__, **expense_details}
        )

    return expenses_with_details

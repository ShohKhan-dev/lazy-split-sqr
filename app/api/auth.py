from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.models import User
from app.database import get_db
from pydantic import BaseModel
from passlib.context import CryptContext

router = APIRouter()


class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user is None or db_user.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    return {"status": "success", "user_id": db_user.user_id, "email": db_user.email}

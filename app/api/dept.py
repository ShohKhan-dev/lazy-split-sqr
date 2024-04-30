from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models import Dept, ExpenseParticipant, Expense, Group, User, GroupMembership
from app.database import get_db
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List


class DeptCreate(BaseModel):
    user_id: int
    lender_id: int
    expense_id: int
    amount: int


class DeptPaid(BaseModel):
    amount: int


router = APIRouter()


@router.get("/{group_id}")
def list_group_depts(group_id: int, db: Session = Depends(get_db)):
    depts = db.query(Dept).filter(Dept.group_id == group_id).all()
    if not depts:
        return {}
    return depts


@router.get("/{group_id}/{user_id}")
def list_user_depts(group_id: int, user_id: int, db: Session = Depends(get_db)):
    depts = (
        db.query(Dept)
        .filter(
            Dept.group_id == group_id,
            or_(Dept.user_id == user_id, Dept.lender_id == user_id),
        )
        .all()
    )
    if not depts:
        raise HTTPException(
            status_code=404, detail="No depts found for the given user ID"
        )
    return depts


@router.delete("/{dept_id}")
def delete_dept(dept_id: int, db: Session = Depends(get_db)):
    dept = db.query(Dept).filter(Dept.dept_id == dept_id).first()

    if dept is None:
        raise HTTPException(status_code=404, detail="Dept not found")

    db.delete(dept)
    db.commit()
    return {"message": "Dept deleted successfully"}


@router.patch("/{dept_id}")
def update_dept_amount(
    dept_id: int, dept_paid: DeptPaid, db: Session = Depends(get_db)
):
    existing_dept = db.query(Dept).filter(Dept.dept_id == dept_id).first()

    if existing_dept is None:
        raise HTTPException(status_code=404, detail="Dept not found")

    existing_dept.amount = existing_dept.amount - dept_paid.amount

    if existing_dept.amount <= 0:
        db.delete(existing_dept)
        db.commit()
        return {"message": "Dept completely paid successfully"}
    else:
        db.commit()
        db.refresh(existing_dept)
        return {
            "message": "Dept updated successfully, amount left: {}".format(
                existing_dept.amount
            )
        }

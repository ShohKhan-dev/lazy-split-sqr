from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, joinedload
from app.models import Dept, Group, Expense, ExpenseParticipant, GroupMembership
from app.database import get_db
from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    group_id: int
    description: str
    amount: int
    created_by: int


class CreateExpenseParticipant(BaseModel):
    expense_id: int
    user_id: int
    amount_paid: int


class CreateDept(BaseModel):
    user_id: int
    lender_id: int
    group_id: int
    amount: float


router = APIRouter()


@router.get("/")
def get_expenses(db: Session = Depends(get_db)):
    return db.query(Expense).all()


@router.get("/{expense_id}")
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = (
        db.query(Expense)
        .options(joinedload(Expense.expense_participants))
        .filter(Expense.expense_id == expense_id)
        .first()
    )
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.post("/")
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    if (
        db.query(GroupMembership)
        .filter(
            and_(
                GroupMembership.user_id == expense.created_by,
                GroupMembership.group_id == expense.group_id,
            )
        )
        .first()
        is None
    ):
        raise HTTPException(status_code=404, detail="User not in Group")

    group = db.query(Group).filter(Group.group_id == expense.group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    db_expense = Expense(**expense.dict())
    db.add(db_expense)
    db.commit()

    # Update total expense of the group
    group.total_expenses += expense.amount
    db.commit()

    db.refresh(db_expense)
    expense_data = {
        "expense_id": db_expense.expense_id,
        "group_id": db_expense.group_id,
        "description": db_expense.description,
        "amount": db_expense.amount,
        "created_by": db_expense.created_by,
        "created_at": db_expense.created_at,
    }

    # Update dept of group members
    mean_value = expense.amount / group.total_members

    members = (
        db.query(GroupMembership.user_id)
        .filter(GroupMembership.group_id == db_expense.group_id)
        .all()
    )
    member_ids = [m.user_id for m in members]

    depts = (
        db.query(Dept)
        .filter(
            Dept.group_id == db_expense.group_id,
            or_(
                Dept.lender_id == db_expense.created_by,
                Dept.user_id == db_expense.created_by,
            ),
        )
        .all()
    )

    dept_index = {(d.lender_id, d.user_id): d for d in depts}

    for member_id in member_ids:
        if member_id == db_expense.created_by:
            continue

        key_by_payer = (db_expense.created_by, member_id)
        key_to_payer = (member_id, db_expense.created_by)

        flag = False
        if key_by_payer in dept_index:
            dept_index[key_by_payer].amount += mean_value
            flag = True

        if key_to_payer in dept_index:
            flag = True
            if dept_index[key_to_payer].amount > mean_value:
                dept_index[key_to_payer].amount -= mean_value
            elif mean_value - dept_index[key_to_payer].amount >= 0.01:
                new_dept = Dept(
                    user_id=member_id,
                    lender_id=db_expense.created_by,
                    group_id=db_expense.group_id,
                    amount=mean_value - dept_index[key_to_payer].amount,
                )
                db.add(new_dept)
                db.delete(dept_index[key_to_payer])
            else:
                db.delete(dept_index[key_to_payer])

        if not flag:
            new_dept = Dept(
                user_id=member_id,
                lender_id=db_expense.created_by,
                group_id=db_expense.group_id,
                amount=mean_value,
            )
            db.add(new_dept)

    db.commit()

    return expense_data


# Delete an expense
@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(Expense.expense_id == expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Update total expense of the group
    group_id = expense.group_id
    group = db.query(Group).filter(Group.group_id == group_id).first()

    group.total_expenses -= expense.amount
    db.commit()

    # Update dept of group members
    mean_value = expense.amount / group.total_members

    members = (
        db.query(GroupMembership.user_id)
        .filter(GroupMembership.group_id == expense.group_id)
        .all()
    )
    member_ids = [m.user_id for m in members]

    depts = (
        db.query(Dept)
        .filter(
            Dept.group_id == expense.group_id,
            or_(
                Dept.lender_id == expense.created_by, Dept.user_id == expense.created_by
            ),
        )
        .all()
    )

    dept_index = {(d.lender_id, d.user_id): d for d in depts}

    for member_id in member_ids:
        if member_id == expense.created_by:
            continue

        key_by_payer = (expense.created_by, member_id)
        key_to_payer = (member_id, expense.created_by)

        if key_to_payer in dept_index:
            dept_index[key_to_payer].amount += mean_value

        if key_by_payer in dept_index:
            if dept_index[key_by_payer].amount > mean_value:
                dept_index[key_by_payer].amount -= mean_value
            elif mean_value - dept_index[key_by_payer].amount >= 0.01:
                new_dept = Dept(
                    user_id=expense.created_by,
                    lender_id=member_id,
                    group_id=expense.group_id,
                    amount=mean_value - dept_index[key_by_payer].amount,
                )
                db.add(new_dept)
                db.delete(dept_index[key_by_payer])
            else:
                db.delete(dept_index[key_by_payer])

    db.commit()

    expense_participants = (
        db.query(ExpenseParticipant)
        .filter(ExpenseParticipant.expense_id == expense.expense_id)
        .all()
    )

    for expense_participant in expense_participants:
        db.delete(expense_participant)
        db.commit()

    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}


@router.post("/participant")
def create_expense_participant(
    p: CreateExpenseParticipant, db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(Expense.expense_id == p.expense_id).first()
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    group = db.query(Group).filter(Group.group_id == expense.group_id).first()

    average_amount = expense.amount / group.total_members
    amount_owed = p.amount_paid - average_amount

    expense_participant = ExpenseParticipant(
        expense_id=p.expense_id,
        user_id=p.user_id,
        amount_paid=p.amount_paid,
        amount_owed=amount_owed,
    )

    db.add(expense_participant)
    db.commit()

    db.refresh(expense_participant)
    return expense_participant

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload
from app.models import Group, User, GroupMembership
from app.database import get_db
from pydantic import BaseModel

router = APIRouter()


class GroupCreate(BaseModel):
    group_name: str
    created_by: int


@router.get("/")
def get_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()


@router.get("/{group_id}")
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).options(joinedload(Group.groupmembers), joinedload(Group.groupexpenses)).filter(
        Group.group_id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.post("/")
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.user_id == group.created_by).first() is None:
        raise HTTPException(status_code=404, detail="User not found")

    db_group = Group(**group.dict())
    db.add(db_group)
    db.commit()

    db.refresh(db_group)
    group_membership = GroupMembership(group_id=db_group.group_id, user_id=group.created_by, is_admin=True)
    db.add(group_membership)
    db.commit()

    db.refresh(db_group)
    return db_group


@router.post("/{group_id}/add_member/{user_id}")
def add_group_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    if db.query(User).filter(User.user_id == user_id).first() is None:
        raise HTTPException(status_code=404, detail="User not found")

    group = db.query(Group).filter(Group.group_id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    if db.query(GroupMembership).filter(
            and_(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id)).first():
        raise HTTPException(status_code=404, detail="Already in group")

    # Update total members of the group
    group.total_members += 1
    db.commit()

    group_membership = GroupMembership(group_id=group_id, user_id=user_id)
    db.add(group_membership)
    db.commit()

    db.refresh(group_membership)
    return group_membership

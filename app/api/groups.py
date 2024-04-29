from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from app.models import Group, User, GroupMembership
from app.database import get_db
from pydantic import BaseModel

router = APIRouter()


class GroupCreate(BaseModel):
    group_name: str
    created_by: int



@router.post("/")
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

    group_data = {
        "group_id": db_group.group_id,
        "group_name": db_group.group_name,
        "created_by": db_group.created_by,
        "created_at": db_group.created_at,
    }

    return group_data


@router.get("/{group_id}")
def get_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).options(joinedload(Group.groupmembers), joinedload(Group.groupexpenses)).filter(Group.group_id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@router.get("/")
def get_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()


@router.post("/{group_id}/add_member/{user_id}")
def add_group_member(group_id: int, user_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    membership = db.query(GroupMembership).filter_by(group_id=group_id, user_id=user_id).first()

    if membership:
        raise HTTPException(status_code=409, detail="User is already a member of the group")
    
    # Update total members of the group
    group.total_members += 1
    db.commit()

    group_membership = GroupMembership(group_id=group_id, user_id=user_id)
    db.add(group_membership)
    db.commit()
    db.refresh(group_membership)
    return group_membership


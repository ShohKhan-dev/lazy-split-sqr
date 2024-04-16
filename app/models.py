
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)

    groupmembers = relationship("GroupMembership", back_populates="user")

class Group(Base):
    __tablename__ = "groups"

    group_id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String, index=True)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.now)

    total_expenses = Column(Integer, default=0)
    total_members = Column(Integer, default=1)

    groupmembers = relationship("GroupMembership", back_populates="group")
    groupexpenses = relationship("Expense", back_populates="group")


class GroupMembership(Base):
    __tablename__ = "group_memberships"

    membership_id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.group_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    is_admin = Column(Boolean, default=False)

    group = relationship("Group", back_populates="groupmembers")
    user = relationship("User", back_populates="groupmembers")

class Expense(Base):
    __tablename__ = "expenses"

    expense_id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.group_id"))
    description = Column(String)
    amount = Column(Integer)
    created_by = Column(Integer, ForeignKey("users.user_id"))
    created_at = Column(DateTime, default=datetime.now)
    group = relationship("Group", back_populates="groupexpenses")


class ExpenseParticipant(Base):
    __tablename__ = "expense_participants"

    expense_participant_id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.expense_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    amount_paid = Column(Integer)
    amount_owed = Column(Integer)
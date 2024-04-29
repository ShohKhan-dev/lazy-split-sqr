import unittest
import pytest

from fastapi import HTTPException, status

from app.api.auth import UserLogin, login
from app.api.users import UserCreate, get_user, create_user, get_user_groups, get_user_expenses
from app.api.groups import GroupCreate, get_group, create_group, add_group_member
from app.api.expenses import get_expense, create_expense, delete_expense, create_expense_participant, \
    ExpenseCreate, CreateExpenseParticipant
from app.models import User, Group, GroupMembership, Expense, ExpenseParticipant
from sqlalchemy import create_engine, StaticPool

from sqlalchemy.orm import sessionmaker
from app.database import Base

DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class TestAuthAPI(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    def test_login_no_user(self):
        user_author = UserLogin(username="Test User", password="password")
        with pytest.raises(HTTPException) as exc_info:
            login(user_author, db=self.db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in str(exc_info.value.detail)

    def test_login_wrong_password(self):
        user = User(username="Test User", password="password1", email="test@example.com")
        self.db.add(user)
        self.db.commit()

        user_author = UserLogin(username="Test User", password="password")
        with pytest.raises(HTTPException) as exc_info:
            login(user_author, db=self.db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in str(exc_info.value.detail)

    def test_login_success(self):
        user = User(username="Test User", password="password", email="test@example.com")
        self.db.add(user)
        self.db.commit()

        user_author = UserLogin(username="Test User", password="password")
        data = login(user_author, db=self.db)

        assert data["status"] == "success"
        assert data["user_id"] == user.user_id
        assert data["email"] == user.email


class TestUserAPI(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    def test_get_user_not_found(self):
        with pytest.raises(HTTPException) as exc_info:
            get_user(user_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)

    def test_get_user_success(self):
        user = User(username="testuser1", password="testpass1", email="test1@example.com")
        self.db.add(user)
        self.db.commit()

        data = get_user(user_id=1, db=self.db)

        assert data.username == user.username
        assert data.password == user.password
        assert data.email == user.email

    def test_create_user_exist_username(self):
        user = User(username="testuser1", password="testpass1", email="test1@example.com")
        self.db.add(user)
        self.db.commit()

        with pytest.raises(HTTPException) as exc_info:
            user_create = UserCreate(username="testuser1", email="new@example.com", password="password")
            create_user(user_create, db=self.db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already exists" in str(exc_info.value.detail)

    def test_create_user_exist_email(self):
        user = User(username="testuser1", password="testpass1", email="test1@example.com")
        self.db.add(user)
        self.db.commit()

        with pytest.raises(HTTPException) as exc_info:
            user_create = UserCreate(username="new_user", email="test1@example.com", password="password")
            create_user(user_create, db=self.db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in str(exc_info.value.detail)

    def test_create_user_success(self):
        user_create = UserCreate(username="new_user", email="test1@example.com", password="password")
        data = create_user(user_create, db=self.db)

        assert data.username == user_create.username
        assert data.username == user_create.username
        assert data.password == user_create.password
        assert data.user_id == 1

        user = self.db.query(User).first()

        assert user.username == user_create.username
        assert user.username == user_create.username
        assert user.password == user_create.password
        assert user.user_id == 1

    def test_get_user_groups_no_user(self):
        with pytest.raises(HTTPException) as exc_info:
            get_user_groups(user_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)

    def test_get_user_groups_no_group(self):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        self.db.add_all([group, user])
        self.db.commit()

        data = get_user_groups(user_id=1, db=self.db)

        assert len(data) == 0

    def test_get_user_groups_success(self):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        group_membership = GroupMembership(group_id=1, user_id=1, is_admin=False)
        self.db.add_all([group, user, group_membership])
        self.db.commit()

        data = get_user_groups(user_id=1, db=self.db)

        assert len(data) == 1

    def test_get_user_expenses_no_user(self):
        with pytest.raises(HTTPException) as exc_info:
            get_user_expenses(user_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)

    def test_get_user_expenses_success(self):
        expense_participant = ExpenseParticipant(expense_participant_id=1, expense_id=1, user_id=1, amount_paid=100,
                                                 amount_owed=1000)
        expense = Expense(expense_id=1, group_id=1, amount=110, description="desc")
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        self.db.add_all([expense_participant, expense, user])
        self.db.commit()

        data = get_user_expenses(user_id=1, db=self.db)

        assert data[0]['expense_description'] == expense.description
        assert data[0]['expense_amount'] == expense.amount
        assert data[0]['amount_paid'] == expense_participant.amount_paid
        assert data[0]['amount_owed'] == expense_participant.amount_owed
        assert data[0]['expense_participant_id'] == expense_participant.expense_participant_id
        assert data[0]['expense_id'] == expense_participant.expense_id
        assert data[0]['user_id'] == expense_participant.user_id


class TestGroupAPI(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    def test_get_group_not_found(self):
        with pytest.raises(HTTPException) as exc_info:
            get_group(group_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "Group not found" in str(exc_info.value.detail)

    def test_get_group_success(self):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        self.db.add(group)
        self.db.commit()

        data = get_group(group_id=1, db=self.db)

        assert data.group_id == group.group_id
        assert data.group_name == group.group_name
        assert data.created_by == group.created_by

    def test_create_group_no_user(self):
        with pytest.raises(HTTPException) as exc_info:
            group_create_data = {"group_name": "Test Group", "created_by": 1}
            create_group(GroupCreate(**group_create_data), db=self.db)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)

    def test_create_group_success(self):
        user = User(user_id=1, username="testuser1", password="testpass1", email="test1@example.com")
        self.db.add(user)
        self.db.commit()

        group_create_data = GroupCreate(group_name="Test Group", created_by=1)
        data = create_group(group_create_data, db=self.db)

        assert isinstance(data, dict)
        assert data['group_name'] == group_create_data.group_name
        assert data['created_by'] == group_create_data.created_by
        assert data['group_id'] == 1

        group = self.db.query(Group).first()

        assert group.group_name == group_create_data.group_name
        assert group.created_by == group_create_data.created_by
        assert group.group_id == 1

        group_membership = self.db.query(GroupMembership).first()

        assert group_membership.group_id == data['group_id']
        assert group_membership.user_id == user.user_id

    def test_add_group_member_no_user(self):
        with pytest.raises(HTTPException) as exc_info:
            add_group_member(group_id=1, user_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)

    def test_add_group_member_no_group(self):
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        self.db.add(user)
        self.db.commit()
        with pytest.raises(HTTPException) as exc_info:
            add_group_member(group_id=1, user_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "Group not found" in str(exc_info.value.detail)

    def test_add_group_member_already(self):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        group_membership = GroupMembership(group_id=1, user_id=1, is_admin=False)
        self.db.add_all([group, user, group_membership])
        self.db.commit()

        with pytest.raises(HTTPException) as exc_info:
            add_group_member(group_id=1, user_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "Already in group" in str(exc_info.value.detail)

    def test_add_group_member_success(self):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        self.db.add_all([group, user])
        self.db.commit()

        data = add_group_member(group_id=1, user_id=1, db=self.db)

        assert data.group_id == group.group_id
        assert data.user_id == user.user_id
        assert data.membership_id == 1

        group_membership = self.db.query(GroupMembership).first()

        assert group_membership.group_id == group.group_id
        assert group_membership.user_id == user.user_id
        assert group_membership.membership_id == 1

        self.db.refresh(group)

        assert group.total_members == 2


class TestExpenseAPI(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    def test_get_expense_not_found(self):
        with pytest.raises(HTTPException) as exc_info:
            get_expense(expense_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "Expense not found" in str(exc_info.value.detail)

    def test_get_expense_success(self):
        expense = Expense(expense_id=1, group_id=1, amount=110, description="desc")
        self.db.add(expense)
        self.db.commit()

        data = get_expense(expense_id=1, db=self.db)

        assert data.expense_id == expense.expense_id
        assert data.group_id == expense.group_id
        assert data.amount == expense.amount
        assert data.description == expense.description

    def test_create_expense_no_user(self):
        with pytest.raises(HTTPException) as exc_info:
            expense_create_data = {"group_id": 1, "description": "Test Expense", "amount": 100, "created_by": 1}
            create_expense(ExpenseCreate(**expense_create_data), db=self.db)

        assert exc_info.value.status_code == 404
        assert "User not in Group" in str(exc_info.value.detail)

    def test_create_expense_no_group(self):
        group_membership = GroupMembership(group_id=1, user_id=1, is_admin=False)
        self.db.add(group_membership)
        self.db.commit()

        with pytest.raises(HTTPException) as exc_info:
            expense_create_data = {"group_id": 1, "description": "Test Expense", "amount": 100, "created_by": 1}
            create_expense(ExpenseCreate(**expense_create_data), db=self.db)

        assert exc_info.value.status_code == 404
        assert "Group not found" in str(exc_info.value.detail)

    def test_create_expense_success(self):
        group_membership = GroupMembership(group_id=1, user_id=1, is_admin=False)
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        self.db.add_all([group_membership, group])
        self.db.commit()

        expense_create_data = ExpenseCreate(group_id=1, created_by=1, description="desc", amount=100)
        data = create_expense(expense_create_data, db=self.db)

        assert data['expense_id'] == 1
        assert data['group_id'] == expense_create_data.group_id
        assert data['created_by'] == expense_create_data.created_by
        assert data['description'] == expense_create_data.description
        assert data['amount'] == expense_create_data.amount

        expense = self.db.query(Expense).first()

        assert expense.expense_id == 1
        assert expense.group_id == expense_create_data.group_id
        assert expense.created_by == expense_create_data.created_by
        assert expense.description == expense_create_data.description
        assert expense.amount == expense_create_data.amount

        self.db.refresh(group)

        assert group.total_expenses == expense_create_data.amount

    def test_delete_expense_no_expense(self):
        with pytest.raises(HTTPException) as exc_info:
            delete_expense(expense_id=1, db=self.db)

        assert exc_info.value.status_code == 404
        assert "Expense not found" in str(exc_info.value.detail)

    def test_delete_expense_success(self):
        expense_participant = ExpenseParticipant(expense_participant_id=1, expense_id=1, user_id=1, amount_paid=100,
                                                 amount_owed=1000)
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1, total_expenses=100)
        expense = Expense(expense_id=1, group_id=1, amount=100, description="desc")
        self.db.add_all([expense_participant, group, expense])
        self.db.commit()

        data = delete_expense(expense_id=1, db=self.db)

        assert data == {"message": "Expense deleted successfully"}

        assert self.db.query(ExpenseParticipant).first() is None
        assert self.db.query(Expense).first() is None

        self.db.refresh(group)

        assert group.total_expenses == 0

    def test_create_expense_participant_no_expense(self):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        self.db.add(group)
        self.db.commit()

        with pytest.raises(HTTPException) as exc_info:
            expense_create_data = {"expense_id": 1, "user_id": 1, "amount_paid": 100}
            create_expense_participant(CreateExpenseParticipant(**expense_create_data), db=self.db)

        assert exc_info.value.status_code == 404
        assert "Expense not found" in str(exc_info.value.detail)

    def test_create_expense_participant_success(self):
        expense = Expense(expense_id=1, group_id=1, amount=100, description="desc")
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=2)
        self.db.add_all([group, expense])
        self.db.commit()

        expense_create_data = CreateExpenseParticipant(expense_id=1, user_id=1, amount_paid=100)
        data = create_expense_participant(expense_create_data, db=self.db)

        assert data.expense_id == expense_create_data.expense_id
        assert data.user_id == expense_create_data.user_id
        assert data.amount_paid == expense_create_data.amount_paid
        assert data.amount_owed == 50

        expense_participant = self.db.query(ExpenseParticipant).first()

        assert expense_participant.expense_id == expense_create_data.expense_id
        assert expense_participant.user_id == expense_create_data.user_id
        assert expense_participant.amount_paid == expense_create_data.amount_paid
        assert expense_participant.amount_owed == 50

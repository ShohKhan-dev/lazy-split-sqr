from app.api.users import *
from app.api.groups import *
from app.api.expenses import *
from app.models import  *
from fastapi import HTTPException, status
from unittest.mock import MagicMock
import pytest

class TestUserAPI:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_create_user_username_exists(self, mock_db):
        # Mock an existing user with the same username
        mock_db.query().filter().first.return_value = User(username="existing_user", email="existing@example.com", password="password")

        user_create = UserCreate(username="existing_user", email="new@example.com", password="password")

        with pytest.raises(HTTPException) as exc_info:
            create_user(user_create, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already exists" in str(exc_info.value.detail)

    def test_create_user_email_exists(self, mock_db):
        # Mock an existing user with the same email
        mock_db.query().filter().first.side_effect = [None, User(username="new_user", email="existing@example.com", password="password")]

        user_create = UserCreate(username="new_user", email="existing@example.com", password="password")

        with pytest.raises(HTTPException) as exc_info:
            create_user(user_create, db=mock_db)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in str(exc_info.value.detail)

    def test_create_user_success(self, mock_db):
        # Mock no existing user with the same username or email
        mock_db.query().filter().first.return_value = None

        user_create = UserCreate(username="new_user", email="new@example.com", password="password")

        created_user = create_user(user_create, db=mock_db)

        assert isinstance(created_user, User)
        assert created_user.username == "new_user"
        assert created_user.email == "new@example.com"
        assert created_user.password == "password"  # Ensure no hashing is applied in this test scenario

    def test_get_user_not_found(self, mock_db):
        # Mock no user found
        mock_db.query().filter().first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_user(user_id=1, db=mock_db)

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)


class TestGroupAPI:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()


    def test_create_group(self, mock_db):
        group_create_data = {"group_name": "Test Group", "created_by": 1}
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = Group(group_id=1, **group_create_data)

        group = create_group(GroupCreate(**group_create_data), db=mock_db)

        assert isinstance(group, Group)
        assert group.group_name == "Test Group"
        assert group.created_by == 1


    def test_get_group(self, mock_db):
        mock_db.query().options().filter().first.return_value = Group(group_id=1, group_name="Test Group", created_by=1)

        group = get_group(group_id=1, db=mock_db)

        assert isinstance(group, Group)
        assert group.group_name == "Test Group"
        assert group.created_by == 1


    def test_get_groups(self, mock_db):
        mock_db.query().all.return_value = [
            Group(group_id=1, group_name="Group 1", created_by=1),
            Group(group_id=2, group_name="Group 2", created_by=2)
        ]

        groups = get_groups(db=mock_db)

        assert len(groups) == 2
        assert groups[0].group_name == "Group 1"
        assert groups[1].group_name == "Group 2"


    def test_add_group_member(self, mock_db):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        mock_db.query().filter().first.side_effect = [user, group]
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = GroupMembership(group_id=1, user_id=1)

        group_membership = add_group_member(group_id=1, user_id=1, db=mock_db)

        assert isinstance(group_membership, GroupMembership)
        assert group_membership.group_id == 1
        assert group_membership.user_id == 1



class TestExpenseAPI:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_create_expense(self, mock_db):
        expense_create_data = {"group_id": 1, "description": "Test Expense", "amount": 100, "created_by": 1}
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = Expense(expense_id=1, **expense_create_data)

        expense = create_expense(ExpenseCreate(**expense_create_data), db=mock_db)

        assert isinstance(expense, Expense)
        assert expense.description == "Test Expense"
        assert expense.amount == 100
        assert expense.created_by == 1

    def test_get_expense(self, mock_db):
        mock_db.query().options().filter().first.return_value = Expense(expense_id=1, group_id=1, description="Test Expense", amount=100, created_by=1)

        expense = get_expense(expense_id=1, db=mock_db)

        assert isinstance(expense, Expense)
        assert expense.description == "Test Expense"
        assert expense.amount == 100
        assert expense.created_by == 1

    def test_delete_expense(self, mock_db):
        expense = Expense(expense_id=1, group_id=1, description="Test Expense", amount=100, created_by=1)
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1, total_expenses=100)
        mock_db.query().filter().first.side_effect = [expense, group]
        mock_db.commit.return_value = None

        response = delete_expense(expense_id=1, db=mock_db)

        assert response == {"message": "Expense deleted successfully"}

    def test_create_expense_participant(self, mock_db):
        expense = Expense(expense_id=1, group_id=1, description="Test Expense", amount=100, created_by=1)
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        mock_db.query().filter().first.side_effect = [user, expense, group]
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = ExpenseParticipant(expense_id=1, user_id=1, amount_paid=100, amount_owed=0)

        expense_participant = create_expense_participant(expense_id=1, user_id=1, amount_paid=100, db=mock_db)

        assert isinstance(expense_participant, ExpenseParticipant)
        assert expense_participant.expense_id == 1
        assert expense_participant.user_id == 1
        assert expense_participant.amount_paid == 100
        assert expense_participant.amount_owed == 0
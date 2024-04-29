from app.api.users import UserCreate, get_users, get_user, create_user, get_user_groups, get_user_expenses
from app.api.groups import GroupCreate, get_groups, get_group, create_group, add_group_member
from app.api.expenses import get_expenses, get_expense, create_expense, delete_expense, create_expense_participant, \
    ExpenseCreate
from app.models import User, Group, GroupMembership, Expense, ExpenseParticipant
from unittest.mock import MagicMock
import pytest


class TestUserAPI:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_get_users(self, mock_db):
        mock_db.query().all.return_value = [
            User(user_id=1, username="User 1", email="test1@example.com", password="password1"),
            User(user_id=2, username="User 2", email="test2@example.com", password="password2")
        ]

        data = get_users(db=mock_db)

        assert len(data) == 2
        assert data[0].username == "User 1"
        assert data[1].username == "User 2"

    def test_get_user(self, mock_db):
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        mock_db.query().filter().first.return_value = user

        data = get_user(user_id=1, db=mock_db)

        assert isinstance(data, User)
        assert data.username == user.username
        assert data.email == user.email
        assert data.password == user.password

    def test_create_user(self, mock_db):
        mock_db.query().filter().first.return_value = None

        user_create = UserCreate(username="new_user", email="new@example.com", password="password")
        data = create_user(user_create, db=mock_db)

        assert isinstance(data, User)
        assert data.username == user_create.username
        assert data.email == user_create.email
        assert data.password == user_create.password

    def test_get_user_groups(self, mock_db):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        mock_db.query().filter().first.return_value = user
        mock_db.query().join().filter().all.return_value = [group]

        data = get_user_groups(user_id=1, db=mock_db)

        assert isinstance(data[0], Group)
        assert data[0].group_name == group.group_name
        assert data[0].created_by == group.created_by
        assert data[0].total_members == group.total_members

    def test_get_user_expenses(self, mock_db):
        mock_user = MagicMock()
        mock_db.user_id = 1
        mock_db.query().filter().first.return_value = mock_user

        # Mock expenses and expense details
        mock_expense_participant = MagicMock()
        mock_expense_participant.expense_id = 1
        mock_expense_participant.participant_info = "info"  # Mocked expense participant info
        mock_db.query().filter().all.return_value = [mock_expense_participant]

        mock_expense = MagicMock()
        mock_expense.description = "Test expense"
        mock_expense.amount = 100
        mock_db.query().filter().first.return_value = mock_expense

        # Call the function with a user_id
        expenses_with_details = get_user_expenses(user_id=1, db=mock_db)

        # Assert that the function returns the expected expenses with details
        assert len(expenses_with_details) == 1
        assert expenses_with_details[0]["participant_info"] == "info"
        assert expenses_with_details[0]["expense_description"] == "Test expense"
        assert expenses_with_details[0]["expense_amount"] == 100


class TestGroupAPI:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_get_groups(self, mock_db):
        mock_db.query().all.return_value = [
            Group(group_id=1, group_name="Group 1", created_by=1),
            Group(group_id=2, group_name="Group 2", created_by=2)
        ]

        data = get_groups(db=mock_db)

        assert len(data) == 2
        assert data[0].group_name == "Group 1"
        assert data[1].group_name == "Group 2"

    def test_get_group(self, mock_db):
        group = Group(group_id=1, group_name="Test Group", created_by=1)
        mock_db.query().options().filter().first.return_value = group

        data = get_group(group_id=1, db=mock_db)

        assert isinstance(data, Group)
        assert data.group_name == group.group_name
        assert data.created_by == group.created_by

    def test_create_group(self, mock_db):
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        mock_db.query().filter().first.return_value = user

        group_create_data = {"group_name": "Test Group", "created_by": 1}
        data = create_group(GroupCreate(**group_create_data), db=mock_db)

        assert isinstance(data, Group)
        assert data.group_name == "Test Group"
        assert data.created_by == 1

    def test_add_group_member(self, mock_db):
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        user = User(user_id=1, username="Test User", email="test@example.com", password="password")
        mock_db.query().filter().first.side_effect = [user, group, None]

        data = add_group_member(group_id=1, user_id=1, db=mock_db)

        assert isinstance(data, GroupMembership)
        assert data.group_id == group.group_id
        assert data.user_id == user.user_id


class TestExpenseAPI:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_get_expenses(self, mock_db):
        expense = Expense(expense_id=1, group_id=1, description="Test Expense", amount=100, created_by=1)
        mock_db.query().all.return_value = [expense]

        data = get_expenses(db=mock_db)

        assert isinstance(data[0], Expense)
        assert data[0].description == expense.description
        assert data[0].amount == expense.amount
        assert data[0].created_by == expense.created_by

    def test_get_expense(self, mock_db):
        expense = Expense(expense_id=1, group_id=1, description="Test Expense", amount=100, created_by=1)
        mock_db.query().options().filter().first.return_value = expense

        data = get_expense(expense_id=1, db=mock_db)

        assert isinstance(data, Expense)
        assert data.description == expense.description
        assert data.amount == expense.amount
        assert data.created_by == expense.created_by

    def test_create_expense(self, mock_db):
        expense = Expense(expense_id=1, group_id=1, description="Test Expense", amount=100, created_by=1)
        mock_db.refresh.return_value = expense

        expense_create_data = {"group_id": 1, "description": "Test Expense", "amount": 100, "created_by": 1}
        data = create_expense(ExpenseCreate(**expense_create_data), db=mock_db)

        assert isinstance(expense, Expense)
        assert data.description == expense.description
        assert data.amount == expense.amount
        assert data.created_by == expense.created_by

    def test_delete_expense(self, mock_db):
        expense = Expense(expense_id=1, group_id=1, description="Test Expense", amount=100, created_by=1)
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1, total_expenses=100)
        mock_db.query().filter().first.side_effect = [expense, group]

        data = delete_expense(expense_id=1, db=mock_db)

        assert data == {"message": "Expense deleted successfully"}

    def test_create_expense_participant(self, mock_db):
        expense = Expense(expense_id=1, group_id=1, description="Test Expense", amount=100, created_by=1)
        group = Group(group_id=1, group_name="Test Group", created_by=1, total_members=1)
        mock_db.query().filter().first.side_effect = [expense, group]

        data = create_expense_participant(expense_id=1, user_id=1, amount_paid=100, db=mock_db)

        assert isinstance(data, ExpenseParticipant)
        assert data.expense_id == expense.expense_id
        assert data.user_id == expense.created_by
        assert data.amount_paid == 100
        assert data.amount_owed == 0

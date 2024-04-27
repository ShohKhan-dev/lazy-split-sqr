 
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import Group, Expense, ExpenseParticipant, User
from app.database import get_db, Base

# Setup the TestClient
client = TestClient(app)

# Setup the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="module")
def override_get_db():
    database = TestingSessionLocal()
    yield database
    database.close()

app.dependency_overrides[get_db] = override_get_db

def test_create_expense():
    group_id = create_test_group()
    response = client.post(
        "/expenses/",
        json={"group_id": group_id, "description": "Test Expense", "amount": 100, "created_by": 1}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Test Expense"
    assert data["amount"] == 100
    assert data["created_by"] == 1
    assert "expense_id" in data

def create_test_group():
    with TestingSessionLocal() as session:
        group = Group(group_name="Test Group", created_by=1)
        session.add(group)
        session.commit()
        session.refresh(group)
        return group.group_id

def test_get_expense():
    expense_id = create_test_expense()
    response = client.get(f"/expenses/{expense_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["expense_id"] == expense_id

def create_test_expense():
    with TestingSessionLocal() as session:
        expense = Expense(group_id=1, description="Test Expense", amount=100, created_by=1)
        session.add(expense)
        session.commit()
        session.refresh(expense)
        return expense.expense_id

def test_get_expenses():
    create_test_expense()
    response = client.get("/expenses/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

def test_delete_expense():
    expense_id = create_test_expense()
    response = client.delete(f"/expenses/{expense_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Expense deleted successfully"
    # Verify expense is deleted
    with TestingSessionLocal() as session:
        expense = session.query(Expense).filter(Expense.expense_id == expense_id).first()
        assert expense is None

def test_create_expense_participant():
    expense_id = create_test_expense()
    user_id = create_test_user()
    response = client.post(
        f"/expenses/participant/?expense_id={expense_id}&user_id={user_id}&amount_paid=50",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["expense_id"] == expense_id
    assert data["user_id"] == user_id

def create_test_user():
    with TestingSessionLocal() as session:
        user = User(username="Test User", email="test@example.com", password="password")
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.user_id

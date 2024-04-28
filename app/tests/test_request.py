import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool

from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import *
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


class TestUser:
    @pytest.fixture
    def client(self):
        # Setup the TestClient
        return TestClient(app)

    @pytest.fixture
    def engine(self):
        # Setup the in-memory SQLite database for testing
        DATABASE_URL = "sqlite:///:memory:"
        return create_engine(
            DATABASE_URL,
            connect_args={
                "check_same_thread": False,
            },
            poolclass=StaticPool,
        )

    @pytest.fixture
    def testing_session(self, engine):
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        return TestingSessionLocal()

    def test_get_users(self, client, testing_session):
        with testing_session as session:
            test_users = [
                User(username="testuser1", password="testpass1", email="test1@example.com"),
                User(username="testuser2", password="testpass2", email="test2@example.com"),
            ]
            session.add_all(test_users)
            session.commit()

        response = client.get("/users/")
        assert response.status_code == 200
        assert len(response.json()) == len(test_users)

    def test_get_single_user(self, client, testing_session):
        with testing_session as session:
            user = User(username="testuser1", password="testpass1", email="test1@example.com")
            session.add(user)
            session.commit()

        response = client.get("/users/1")
        assert response.status_code == 200
        response_text = response.json()
        assert response_text["username"] == "testuser1"
        assert response_text["email"] == "test1@example.com"

    def test_create_user(self, client, testing_session):
        response = client.post(
            "/users/",
            json={"username": "testuser3", "password": "testpass3", "email": "test3@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser3"
        assert data["email"] == "test3@example.com"
        assert "user_id" in data

    def test_get_user_groups(self, client, testing_session):
        with testing_session as session:
            db_group = Group(group_name="TestGroup1", created_by=1)
            session.add(db_group)
            session.commit()
            session.refresh(db_group)

            group_membership = GroupMembership(group_id=db_group.group_id, user_id=1, is_admin=True)
            session.add(group_membership)
            session.commit()
            session.refresh(group_membership)

        response = client.get("/users/1/groups")
        assert response.status_code == 200
        response_text = response.json()
        assert len(response_text) == 1
        assert response_text[0]["group_name"] == "TestGroup1"
        assert response_text[0]["created_by"] == 1


class TestGroup:
    def test_create_group():
        user = User(username="testname", email="test@gmail.com", password="testpass")
        with TestingSessionLocal() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
        response = client.post(
            "/groups/",
            json={"group_name": "TestGroup", "created_by": user.user_id}
        )
        print("RESPONMSE: ", response.text, user.user_id)
        assert response.status_code == 200
        data = response.json()
        assert data["group_name"] == "TestGroup"
        assert data["created_by"] == 1
        assert "group_id" in data


    def test_get_group():
        with TestingSessionLocal() as session:
            group = Group(group_name="TestGroup", created_by=1)
            session.add(group)
            session.commit()

        response = client.get("/groups/1")

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["group_name"] == "TestGroup"
        assert response_data["created_by"] == 1


    def test_get_groups():
        with TestingSessionLocal() as session:
            session.add_all([
                Group(group_name="TestGroup1", created_by=1),
                Group(group_name="TestGroup2", created_by=2)
            ])
            session.commit()

        response = client.get("/groups/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


    def test_add_group_member():
        with TestingSessionLocal() as session:
            session.add(Group(group_name="TestGroup", created_by=1))
            session.add(User(username="TestUser", email="test@example.com", password="password"))
            session.commit()

        response = client.post("/groups/1/add_member/1")

        assert response.status_code == 200
        data = response.json()
        assert data["group_id"] == 1
        assert data["user_id"] == 1
        assert "membership_id" in data

class TestExpenses:
    @staticmethod
    def create_test_user():
        with TestingSessionLocal() as session:
            user = User(username="Test User", email="test@example.com", password="password")
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.user_id
        
    @staticmethod
    def create_test_expense():
        with TestingSessionLocal() as session:
            expense = Expense(group_id=1, description="Test Expense", amount=100, created_by=1)
            session.add(expense)
            session.commit()
            session.refresh(expense)
            return expense.expense_id
        
    def test_create_expense():
        group_id = TestExpenses.create_test_group()
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



    def test_get_expense():
        expense_id = TestExpenses.create_test_expense()
        response = client.get(f"/expenses/{expense_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["expense_id"] == expense_id




    def test_get_expenses():
        TestExpenses.create_test_expense()
        response = client.get("/expenses/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


    def test_delete_expense():
        expense_id = TestExpenses.create_test_expense()
        response = client.delete(f"/expenses/{expense_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Expense deleted successfully"
        # Verify expense is deleted
        with TestingSessionLocal() as session:
            expense = session.query(Expense).filter(Expense.expense_id == expense_id).first()
            assert expense is None


    def test_create_expense_participant():
        expense_id = TestExpenses.create_test_expense()
        user_id = TestExpenses.create_test_user()
        response = client.post(
            f"/expenses/participant/?expense_id={expense_id}&user_id={user_id}&amount_paid=50",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["expense_id"] == expense_id
        assert data["user_id"] == user_id


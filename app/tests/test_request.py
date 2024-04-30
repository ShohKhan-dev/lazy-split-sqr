from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool

from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import User, Group, GroupMembership, Expense
from app.database import get_db, Base

import unittest

# Setup the TestClient
client = TestClient(app)

# Setup the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

test_users = [
    {
        "username": "testuser1",
        "password": "testpass1",
        "email": "test1@example.com",
    },
    {
        "username": "testuser2",
        "password": "testpass2",
        "email": "test2@example.com",
    },
]


class TestAuth(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    def test_login_user(self):
        user = User(
            username="testuser3",
            password="testpass3",
            email="test3@example.com",
        )
        with TestingSessionLocal() as session:
            session.add(user)
            session.commit()
            session.refresh(user)

        response = client.post(
            "/auth/login",
            json={"username": "testuser3", "password": "testpass3"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["user_id"] == user.user_id
        assert data["email"] == user.email


class TestUser(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    def test_get_users(self):
        with TestingSessionLocal() as session:
            session.add_all(
                [
                    User(
                        username="testuser1",
                        password="testpass1",
                        email="test1@example.com",
                    ),
                    User(
                        username="testuser2",
                        password="testpass2",
                        email="test2@example.com",
                    ),
                ]
            )
            session.commit()

        response = client.get("/users/")
        assert response.status_code == 200
        assert len(response.json()) >= len(test_users)

    def test_get_single_user(self):
        user = User(
            username="testuser3",
            password="testpass3",
            email="test3@example.com",
        )
        with TestingSessionLocal() as session:
            session.add(user)
            session.commit()
            session.refresh(user)

        response = client.get(f"/users/{user.user_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["username"] == user.username
        assert data["email"] == user.email
        assert data["user_id"] == user.user_id

    def test_create_user(self):
        response = client.post(
            "/users/",
            json={
                "username": "testuser4",
                "password": "testpass4",
                "email": "test4@example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["username"] == "testuser4"
        assert data["email"] == "test4@example.com"
        assert "user_id" in data

    def test_get_user_groups(self):
        user = User(
            username="testuser5",
            password="testpass5",
            email="test5@example.com",
        )
        db_group = Group(group_name="TestGroup1", created_by=1)

        with TestingSessionLocal() as session:
            session.add(user)
            session.commit()

            db_group.created_by = user.user_id
            session.add(db_group)
            session.commit()
            session.refresh(db_group)

            session.add(
                GroupMembership(
                    group_id=db_group.group_id,
                    user_id=user.user_id,
                    is_admin=True,
                )
            )
            session.commit()

            session.refresh(user)
            session.refresh(db_group)

        print(user.user_id)
        response = client.get(f"/users/{user.user_id}/groups")
        assert response.status_code == 200
        data = response.json()

        assert len(data) >= 1

        ok = False
        for response_group in data:
            if (
                response_group["group_name"] == db_group.group_name
                and response_group["created_by"] == user.user_id
            ):
                ok = True
                break

        assert ok, "User Group not founded"


class TestGroup(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    def test_create_group(self):
        user = User(
            username="testuser6",
            password="testpass6",
            email="test6@example.com",
        )
        with TestingSessionLocal() as session:
            session.add(user)
            session.commit()

            session.refresh(user)

        response = client.post(
            "/groups/",
            json={"group_name": "TestGroup2", "created_by": user.user_id},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["group_name"] == "TestGroup2"
        assert data["created_by"] == user.user_id
        assert "group_id" in data

    def test_get_group(self):
        user = User(
            username="testuser7",
            password="testpass7",
            email="test7@example.com",
        )
        group = Group(group_name="TestGroup3", created_by=1)
        with TestingSessionLocal() as session:
            session.add(user)
            session.commit()
            session.refresh(user)

            group.created_by = user.user_id
            session.add(group)
            session.commit()

            session.refresh(group)
            session.refresh(user)

        response = client.get(f"/groups/{group.group_id}")

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["group_name"] == "TestGroup3"
        assert response_data["created_by"] == user.user_id

    def test_get_groups(self):
        with TestingSessionLocal() as session:
            user_1 = User(
                username="testuser8",
                password="testpass8",
                email="test8@example.com",
            )
            user_2 = User(
                username="testuser9",
                password="testpass9",
                email="test9@example.com",
            )
            session.add_all([user_1, user_2])
            session.commit()
            session.refresh(user_1)
            session.refresh(user_2)

            session.add_all(
                [
                    Group(group_name="TestGroup4", created_by=user_1.user_id),
                    Group(group_name="TestGroup5", created_by=user_2.user_id),
                ]
            )
            session.commit()

        response = client.get("/groups/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_add_group_member(self):
        user = User(
            username="testuser10",
            password="testpass10",
            email="test10@example.com",
        )
        group = Group(group_name="TestGroup6", created_by=1)
        with TestingSessionLocal() as session:
            session.add(user)
            session.commit()
            session.refresh(user)

            group.created_by = user.user_id
            session.add(group)
            session.commit()

            session.refresh(group)
            session.refresh(user)

        response = client.post(
            f"/groups/{group.group_id}/add_member/{user.user_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["group_id"] == group.group_id
        assert data["user_id"] == user.user_id
        assert "membership_id" in data


class TestExpenses(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    @staticmethod
    def create_test_user():
        with TestingSessionLocal() as session:
            user = User(
                username="Test User",
                email="test@example.com",
                password="password",
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.user_id

    @staticmethod
    def create_test_group(user_id):
        with TestingSessionLocal() as session:
            group = Group(
                group_name="Test Group", created_by=user_id, total_expenses=100
            )
            session.add(group)
            session.commit()
            session.refresh(group)
            return group.group_id

    @staticmethod
    def create_test_expense():
        with TestingSessionLocal() as session:
            expense = Expense(
                group_id=1,
                description="Test Expense",
                amount=100,
                created_by=1,
            )
            session.add(expense)
            session.commit()
            session.refresh(expense)
            return expense.expense_id

    def test_get_expenses(self):
        response = client.get("/expenses/")
        assert response.status_code == 200
        cur = len(response.json())

        TestExpenses.create_test_expense()
        response = client.get("/expenses/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == cur + 1

    def test_get_expense(self):
        expense_id = TestExpenses.create_test_expense()
        response = client.get(f"/expenses/{expense_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["expense_id"] == expense_id

    def test_delete_expense(self):
        TestExpenses.create_test_group(1)
        expense_id = TestExpenses.create_test_expense()
        response = client.delete(f"/expenses/{expense_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Expense deleted successfully"
        # Verify expense is deleted
        with TestingSessionLocal() as session:
            expense = (
                session.query(Expense)
                .filter(Expense.expense_id == expense_id)
                .first()
            )
            assert expense is None

    def test_create_expense_participant(self):
        user_id = TestExpenses.create_test_user()
        TestExpenses.create_test_group(user_id)
        expense_id = TestExpenses.create_test_expense()
        response = client.post(
            "/expenses/participant/",
            json={
                "expense_id": expense_id,
                "user_id": user_id,
                "amount_paid": 50,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["expense_id"] == expense_id
        assert data["user_id"] == user_id

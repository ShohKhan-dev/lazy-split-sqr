from hypothesis import given, strategies as st
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from app.database import get_db, Base
from app.main import app
import unittest

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

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Strategies for generating test data
id_strategy = st.integers(min_value=1, max_value=500)
str_strategy = st.text(min_size=1, max_size=50)
email_strategy = st.emails()
amount_strategy = st.integers(min_value=1, max_value=1000)


class TestAuthFuzz(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    @given(username=str_strategy, password=str_strategy)
    def test_create_user(self, username, password):
        response = client.post(
            "/auth/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == 200 or response.status_code == 401


class TestUserFuzz(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    @given(username=str_strategy, password=str_strategy, email=email_strategy)
    def test_create_user(self, username, password, email):
        response = client.post(
            "/users/",
            json={"username": username, "password": password, "email": email},
        )
        assert response.status_code == 200 or response.status_code == 400

    @given(user_id=id_strategy)
    def test_get_user(self, user_id):
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200 or response.status_code == 404

    @given(user_id=id_strategy)
    def test_get_user_groups(self, user_id):
        response = client.get(f"/users/{user_id}/groups")
        assert response.status_code == 200 or response.status_code == 404

    @given(user_id=id_strategy)
    def test_get_user_expenses(self, user_id):
        response = client.get(f"/users/{user_id}/expenses")
        assert response.status_code == 200 or response.status_code == 404


class TestGroupFuzz(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    @given(group_name=str_strategy, created_by=id_strategy)
    def test_create_group(self, group_name, created_by):
        response = client.post(
            "/groups/",
            json={"group_name": group_name, "created_by": created_by},
        )
        assert response.status_code == 200 or response.status_code == 404

    @given(group_id=id_strategy)
    def test_get_group(self, group_id):
        response = client.get(f"/groups/{group_id}")
        assert response.status_code == 200 or response.status_code == 404

    @given(group_id=id_strategy, user_id=id_strategy)
    def test_add_group_member(self, group_id, user_id):
        response = client.post(f"/groups/{group_id}/add_member/{user_id}")
        assert response.status_code == 200 or response.status_code == 404


class TestExpenseFuzz(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        self.db.invalidate()
        self.db.close()

    @given(group_id=id_strategy, description=str_strategy, amount=amount_strategy, created_by=id_strategy)
    def test_create_expense(self, group_id, description, amount, created_by):
        response = client.post(
            "/expenses/",
            json={"group_id": group_id, "description": description, "amount": amount, "created_by": created_by},
        )
        assert response.status_code == 200 or response.status_code == 404

    @given(expense_id=id_strategy)
    def test_get_expense(self, expense_id):
        response = client.get(f"/expenses/{expense_id}")
        assert response.status_code == 200 or response.status_code == 404

    @given(expense_id=id_strategy)
    def test_delete_expense(self, expense_id):
        response = client.delete(f"/expenses/{expense_id}")
        assert response.status_code == 200 or response.status_code == 404

    @given(expense_id=id_strategy, user_id=id_strategy, amount_paid=amount_strategy)
    def test_create_expense_participant(self, expense_id, user_id, amount_paid):
        response = client.post(
            f"/expenses/participant/",
            json={"expense_id": expense_id, "user_id": user_id, "amount_paid": amount_paid}
        )
        assert response.status_code == 200 or response.status_code == 404

 
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import Group, User
from app.database import get_db, Base

# Setup the TestClient
client = TestClient(app)

# Setup the in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module")
def override_get_db():
    database = TestingSessionLocal()
    yield database
    database.close()


app.dependency_overrides[get_db] = override_get_db


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

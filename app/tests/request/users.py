from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from ...app.main import app
from app.models import User, Group, GroupMembership
from app.database import get_db, Base

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
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

test_users = [
    {"username": "testuser1", "password": "testpass1", "email": "test1@example.com"},
    {"username": "testuser2", "password": "testpass2", "email": "test2@example.com"},
]


def override_get_db():
    database = TestingSessionLocal()
    yield database
    database.close()


app.dependency_overrides[get_db] = override_get_db


def test_get_users():
    with TestingSessionLocal() as session:
        for user_data in test_users:
            user = User(**user_data)
            session.add(user)
        session.commit()

    response = client.get("/users/")

    assert response.status_code == 200
    assert len(response.json()) == len(test_users)


def test_get_single_user():
    response = client.get("/users/1")

    assert response.status_code == 200
    response_text = response.json()

    assert response_text["username"] == "testuser1"
    assert response_text["email"] == "test1@example.com"


def test_create_user():
    response = client.post(
        "/users/", json={"username": "testuser3", "password": "testpass3", "email": "test3@example.com"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "testuser3"
    assert data["email"] == "test3@example.com"
    assert "user_id" in data


def test_get_user_groups():
    with TestingSessionLocal() as session:
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

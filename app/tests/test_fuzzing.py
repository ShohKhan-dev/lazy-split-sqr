from fastapi.testclient import TestClient
from app.main import app
import pytest
from hypothesis import given, strategies as st

client = TestClient(app)

# Strategies for generating test data
username_strategy = st.text(min_size=1, max_size=50)
password_strategy = st.text(min_size=1, max_size=50)
email_strategy = st.emails()
user_id_strategy = st.integers(min_value=1, max_value=500)
group_name_strategy = st.text(min_size=1, max_size=2000)
user_id_strategy = st.integers(min_value=1, max_value=500)
group_id_strategy = st.integers(min_value=1, max_value=1000)
description_strategy = st.text(min_size=1, max_size=10000)
amount_strategy = st.integers(min_value=1, max_value=1000)
expense_id_strategy = st.integers(min_value=1, max_value=10000)


@given(username=username_strategy, password=password_strategy, email=email_strategy)
def test_create_user(username, password, email):
    response = client.post(
        "/users/",
        json={"username": username, "password": password, "email": email},
    )
    assert response.status_code == 200 or response.status_code == 400


@given(user_id=user_id_strategy)
def test_get_user(user_id):
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200 or response.status_code == 404


@given(user_id=user_id_strategy)
def test_get_user_groups(user_id):
    response = client.get(f"/users/{user_id}/groups")
    assert response.status_code == 200 or response.status_code == 404


@given(user_id=user_id_strategy)
def test_get_user_expenses(user_id):
    response = client.get(f"/users/{user_id}/expenses")
    assert response.status_code == 200 or response.status_code == 404


@given(group_name=group_name_strategy, created_by=user_id_strategy)
def test_create_group(group_name, created_by):
    response = client.post(
        "/groups/",
        json={"group_name": group_name, "created_by": created_by},
    )
    assert response.status_code == 200 or response.status_code == 404


@given(group_id=group_id_strategy)
def test_get_group(group_id):
    response = client.get(f"/groups/{group_id}")
    assert response.status_code == 200 or response.status_code == 404


@given(group_id=group_id_strategy, user_id=user_id_strategy)
def test_add_group_member(group_id, user_id):
    response = client.post(f"/groups/{group_id}/add_member/{user_id}")
    assert response.status_code == 200 or response.status_code == 404

@given(group_id=group_id_strategy, description=description_strategy, amount=amount_strategy, created_by=user_id_strategy)
def test_create_expense(group_id, description, amount, created_by):
    response = client.post(
        "/expenses/",
        json={"group_id": group_id, "description": description, "amount": amount, "created_by": created_by},
    )
    assert response.status_code == 200 or response.status_code == 404


@given(expense_id=expense_id_strategy)
def test_get_expense(expense_id):
    response = client.get(f"/expenses/{expense_id}")
    assert response.status_code == 200 or response.status_code == 404


@given(expense_id=expense_id_strategy)
def test_delete_expense(expense_id):
    response = client.delete(f"/expenses/{expense_id}")
    assert response.status_code == 200 or response.status_code == 404


@given(expense_id=expense_id_strategy, user_id=user_id_strategy, amount_paid=amount_strategy)
def test_create_expense_participant(expense_id, user_id, amount_paid):
    response = client.post(
        "/expenses/participant/",
        json={"expense_id": expense_id, "user_id": user_id, "amount_paid": amount_paid},
    )
    assert response.status_code == 200 or response.status_code == 422
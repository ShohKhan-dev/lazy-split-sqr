from mocks import *
import pytest
from unittest.mock import patch, MagicMock
from front.main import (
    get_user_groups,
    get_user_expenses,
    get_user_by_username,
    get_user,
    get_group,
    pay_dept_fn,
    name_columns,
    get_group_depts,
    get_user_depts,
    BASE_URL,
)


def test_get_user_groups(requests_mock):
    user_id = 123
    response_json = [
        {"group_id": 1, "name": "Group 1"},
        {"group_id": 2, "name": "Group 2"},
    ]
    requests_mock.get.return_value.json.return_value = response_json

    groups = get_user_groups(user_id)

    requests_mock.get.assert_called_once_with(
        f"{BASE_URL}/users/{user_id}/groups"
    )

    assert groups == response_json


def test_get_user_expenses(requests_mock):
    user_id = 123
    response_json = [
        {"expense_id": 1, "amount": 100},
        {"expense_id": 2, "amount": 200},
    ]
    requests_mock.get.return_value.json.return_value = response_json

    expenses = get_user_expenses(user_id)

    requests_mock.get.assert_called_once_with(
        f"{BASE_URL}/users/{user_id}/expenses"
    )

    assert expenses == response_json


def test_get_user_by_username(requests_mock):
    username = "test_user"
    response_json = {
        "user_id": 123,
        "username": "test_user",
        "email": "test@example.com",
    }
    requests_mock.get.return_value.json.return_value = response_json

    user = get_user_by_username(username)

    requests_mock.get.assert_called_once_with(
        f"{BASE_URL}/users/username/{username}"
    )

    assert user == response_json


def test_get_user(requests_mock):
    user_id = 123
    response_json = {
        "user_id": 123,
        "username": "test_user",
        "email": "test@example.com",
    }
    requests_mock.get.return_value.json.return_value = response_json

    user = get_user(user_id)

    requests_mock.get.assert_called_once_with(f"{BASE_URL}/users/{user_id}")

    assert user == response_json


def test_get_group(requests_mock):
    group_id = 1
    response_json = {"group_id": 1, "name": "Group 1"}
    requests_mock.get.return_value.json.return_value = response_json

    group = get_group(group_id)

    requests_mock.get.assert_called_once_with(f"{BASE_URL}/groups/{group_id}")

    assert group == response_json


def test_pay_dept_fn_success(requests_mock, st_success_mock):
    amount_paid = 100
    dept = {"dept_id": 123}

    requests_mock.patch.return_value.status_code = 200

    callback = pay_dept_fn(amount_paid, dept)
    result = callback()

    requests_mock.patch.assert_called_once_with(
        f"{BASE_URL}/dept/123", json={"amount": amount_paid}
    )
    st_success_mock.assert_called_once_with("OK")

    assert result == {}


def test_pay_dept_fn_failure(requests_mock, st_error_mock):
    amount_paid = 100
    dept = {"dept_id": 123}

    requests_mock.patch.return_value.status_code = 500

    callback = pay_dept_fn(amount_paid, dept)
    result = callback()

    requests_mock.patch.assert_called_once_with(
        f"{BASE_URL}/dept/123", json={"amount": amount_paid}
    )

    st_error_mock.assert_called_once_with("FAIL")
    assert result == {}


@pytest.fixture
def st_text_mock():
    with patch("front.main.st.text") as mock:
        yield mock


def test_name_columns(st_text_mock):
    columns = [MagicMock() for _ in range(3)]
    column_names = ["Column 1", "Column 2", "Column 3"]

    name_columns(columns, column_names)

    st_text_mock.assert_any_call("Column 1")
    st_text_mock.assert_any_call("Column 2")
    st_text_mock.assert_any_call("Column 3")

    assert st_text_mock.call_count == len(column_names)


def test_get_group_depts(requests_mock):
    group_id = 123
    response_data = [
        {"dept_id": 1, "amount": 100},
        {"dept_id": 2, "amount": 200},
    ]
    expected_response = response_data

    requests_mock.get.return_value.status_code = 200
    requests_mock.get.return_value.json.return_value = response_data

    result = get_group_depts(group_id)

    requests_mock.get.assert_called_once_with(f"{BASE_URL}/dept/{group_id}")

    assert result == expected_response


def test_get_user_depts(requests_mock):
    group_id = 123
    user_id = 456
    response_data = [
        {"dept_id": 1, "amount": 100},
        {"dept_id": 2, "amount": 200},
    ]
    expected_response = response_data

    requests_mock.get.return_value.status_code = 200
    requests_mock.get.return_value.json.return_value = response_data

    result = get_user_depts(group_id, user_id)

    requests_mock.get.assert_called_once_with(
        f"{BASE_URL}/dept/{group_id}/{user_id}"
    )

    assert result == expected_response

from mocks import *
from front.main import get_user_groups, get_user_expenses, get_user_by_username, get_user, get_group, BASE_URL

def test_get_user_groups(requests_mock):
    user_id = 123
    response_json = [{"group_id": 1, "name": "Group 1"}, {"group_id": 2, "name": "Group 2"}]
    requests_mock.get.return_value.json.return_value = response_json

    groups = get_user_groups(user_id)


    requests_mock.get.assert_called_once_with(f"{BASE_URL}/users/{user_id}/groups")

    assert groups == response_json


def test_get_user_expenses(requests_mock):
    user_id = 123
    response_json = [{"expense_id": 1, "amount": 100}, {"expense_id": 2, "amount": 200}]
    requests_mock.get.return_value.json.return_value = response_json

    expenses = get_user_expenses(user_id)

    requests_mock.get.assert_called_once_with(f"{BASE_URL}/users/{user_id}/expenses")

    assert expenses == response_json


def test_get_user_by_username(requests_mock):
    username = "test_user"
    response_json = {"user_id": 123, "username": "test_user", "email": "test@example.com"}
    requests_mock.get.return_value.json.return_value = response_json

    user = get_user_by_username(username)

    requests_mock.get.assert_called_once_with(f"{BASE_URL}/users/username/{username}")

    assert user == response_json


def test_get_user(requests_mock):
    user_id = 123
    response_json = {"user_id": 123, "username": "test_user", "email": "test@example.com"}
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
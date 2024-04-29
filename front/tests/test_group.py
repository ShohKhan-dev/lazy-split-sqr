from mocks import *
from front.main import (
    add_member,
    create_expense,
    create_group,
    a_group_display,
    BASE_URL,
)


def test_add_member_success(
    requests_mock, st_success_mock, get_user_by_username_mock
):
    username = "existing_user"
    get_user_by_username_mock.return_value = {"user_id": 123}

    group_id = 1
    response_json = {"user_id": 123}
    requests_mock.post.return_value.json.return_value = response_json

    add_member(group_id, username)

    requests_mock.post.assert_called_once_with(
        f"{BASE_URL}/groups/{group_id}/add_member/123"
    )
    get_user_by_username_mock.assert_called_once_with(username)
    st_success_mock.assert_called_once_with(f"Added {username} to the group")


def test_add_member_user_not_found(st_error_mock, get_user_by_username_mock):
    username = "non_existing_user"
    get_user_by_username_mock.return_value = {}

    add_member(1, username)

    st_error_mock.assert_called_once_with(f"User {username} doesn't exists")


def test_add_member_error_response(
    requests_mock, st_error_mock, get_user_by_username_mock
):
    username = "existing_user"
    get_user_by_username_mock.return_value = {"user_id": 123}

    requests_mock.post.return_value.json.return_value = {}

    add_member(1, username)
    st_error_mock.assert_called_once_with(
        f"Couldn't add {username} to the group"
    )


def test_create_expense_success(
    requests_mock, st_success_mock, st_session_state_mock
):
    group_id = 1
    created_by = 1
    username = "test_user"
    amount = 100
    description = "Test expense"
    response_json = {"expense_id": 123}
    requests_mock.post.return_value.status_code = 200
    requests_mock.post.return_value.json.return_value = response_json
    st_session_state_mock.username = username

    create_expense(group_id, created_by, amount, description)

    requests_mock.post.assert_called_once_with(
        f"{BASE_URL}/expenses",
        json={
            "group_id": group_id,
            "created_by": created_by,
            "amount": amount,
            "description": description,
        },
    )

    st_success_mock.assert_called_once_with(
        f"Expense with {amount} roubles by {username} was created"
    )


def test_create_expense_invalid_amount(requests_mock, st_error_mock):

    create_expense(1, "test_user", 0, "Test expense")

    st_error_mock.assert_called_once_with("Amount should be a positive number")


def test_create_expense_error_response(requests_mock, st_error_mock):
    group_id = 1
    created_by = "test_user"
    amount = 100
    description = "Test expense"
    requests_mock.post.return_value.status_code = 500

    create_expense(group_id, created_by, amount, description)

    st_error_mock.assert_called_once_with("Couldn't create expense")


def test_create_group_success(requests_mock):

    group_name = "Test Group"
    created_by = "test_user"
    response_json = {"group_id": 123}
    requests_mock.post.return_value.status_code = 200
    requests_mock.post.return_value.json.return_value = response_json

    # Call the function
    result = create_group(group_name, created_by)

    # Check if requests.post is called with the correct endpoint and JSON data
    requests_mock.post.assert_called_once_with(
        f"{BASE_URL}/groups/",
        json={"group_name": group_name, "created_by": created_by},
    )

    # Check if the result matches the expected response
    assert result == response_json


def test_create_group_error_response(requests_mock):
    group_name = "Test Group"
    created_by = "test_user"
    requests_mock.post.return_value.status_code = 500

    create_group(group_name, created_by)

    requests_mock.post.assert_called_once()


def test_a_group_display_members(
    get_group_mock, st_radio_mock, members_display_mock, expenses_display_mock
):
    group_id = 123
    group_data = {"group_id": group_id, "group_name": "Test Group"}
    get_group_mock.return_value = group_data

    st_radio_mock.return_value = "Members"

    a_group_display(group_data)

    members_display_mock.assert_called_once_with(group_data)

    expenses_display_mock.assert_not_called()


def test_a_group_display_expenses(
    get_group_mock, st_radio_mock, members_display_mock, expenses_display_mock
):
    group_id = 123
    group_data = {"group_id": group_id, "group_name": "Test Group"}
    get_group_mock.return_value = group_data

    st_radio_mock.return_value = "Expenses"

    a_group_display(group_data)

    expenses_display_mock.assert_called_once_with(group_data)

    members_display_mock.assert_not_called()

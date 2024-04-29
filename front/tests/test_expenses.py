from mocks import *
from front.main import delete_expense_fn, pay_expense_fn, BASE_URL

def test_delete_expense_fn_success(requests_mock, st_success_mock):
    expense_id = 123
    requests_mock.delete.return_value.status_code = 200

    result = delete_expense_fn(expense_id)()

    requests_mock.delete.assert_called_once_with(f"{BASE_URL}/expenses/{expense_id}")

    st_success_mock.assert_called_once_with("Deleted successfully")

    assert result == {}


def test_delete_expense_fn_error(requests_mock, st_error_mock):
    expense_id = 123
    requests_mock.delete.return_value.status_code = 500

    result = delete_expense_fn(expense_id)()

    requests_mock.delete.assert_called_once_with(f"{BASE_URL}/expenses/{expense_id}")

    st_error_mock.assert_called_once_with("Couldn't delete expense")

    assert result == {}


def test_pay_expense_fn_success(requests_mock, st_success_mock):
    expense_id = 123
    user_id = 456
    amount_paid = 100
    requests_mock.post.return_value.status_code = 200

    result = pay_expense_fn(expense_id, user_id, amount_paid)()

    requests_mock.post.assert_called_once_with(
        f"{BASE_URL}/expenses/participant",
        json={"expense_id": expense_id, "user_id": user_id, "amount_paid": amount_paid}
    )

    st_success_mock.assert_called_once_with("Paid successfully")

    assert result == {}


def test_pay_expense_fn_error(requests_mock, st_error_mock):

    expense_id = 123
    user_id = 456
    amount_paid = 100
    requests_mock.post.return_value.status_code = 500

    result = pay_expense_fn(expense_id, user_id, amount_paid)()

    requests_mock.post.assert_called_once_with(
        f"{BASE_URL}/expenses/participant",
        json={"expense_id": expense_id, "user_id": user_id, "amount_paid": amount_paid}
    )

    st_error_mock.assert_called_once_with("Couldn't pay expense")

    assert result == {}
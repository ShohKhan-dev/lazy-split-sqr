from mocks import *
from front.main import register, auth_display, main, login


def test_register_success(requests_mock, st_sidebar_success_mock):
    response_json = {"user_id": 123}
    requests_mock.post.return_value.status_code = 200
    requests_mock.post.return_value.json.return_value = response_json

    register("test@example.com", "test_user", "password")

    st_sidebar_success_mock.assert_called_once_with("Registered successfully")


def test_register_failure(requests_mock, st_sidebar_error_mock):
    requests_mock.post.return_value.status_code = 400
    requests_mock.post.return_value.json.return_value = {
        "error": "Invalid request"
    }

    register("test@example.com", "test_user", "password")

    st_sidebar_error_mock.assert_called_once_with("Registration failed")


def test_login_success(requests_mock, st_sidebar_success_mock):
    response_json = {
        "status": "success",
        "user_id": 123,
        "email": "test@example.com",
        "username": "test_user",
    }
    requests_mock.post.return_value.json.return_value = response_json

    login("test_user", "password")

    st_sidebar_success_mock.assert_called_once_with("Login successful!")


def test_login_failure(requests_mock, st_sidebar_error_mock):
    response_json = {}
    requests_mock.post.return_value.json.return_value = response_json

    login("invalid_user", "invalid_password")

    st_sidebar_error_mock.assert_called_once_with(
        "Login failed. Invalid username or password."
    )


def test_auth_display_register(st_sidebar_radio_mock, st_sidebar_title_mock):
    st_sidebar_radio_mock.return_value = "Register"

    auth_display()

    st_sidebar_title_mock.assert_called_once_with("Registration")


def test_auth_display_login(st_sidebar_radio_mock, st_sidebar_title_mock):
    st_sidebar_radio_mock.return_value = "Login"

    auth_display()

    st_sidebar_title_mock.assert_called_once_with("Login")


def test_main_logged_in(
    st_session_state_mock,
    profile_display_mock,
    groups_display_mock,
    auth_display_mock,
):
    st_session_state_mock.get.return_value = True

    main()

    profile_display_mock.assert_called_once()

    groups_display_mock.assert_called_once()

    auth_display_mock.assert_not_called()


def test_main_not_logged_in(
    st_session_state_mock,
    profile_display_mock,
    groups_display_mock,
    auth_display_mock,
):

    st_session_state_mock.get.return_value = False

    main()

    profile_display_mock.assert_not_called()

    groups_display_mock.assert_not_called()

    auth_display_mock.assert_called_once()

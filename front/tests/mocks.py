import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def st_sidebar_title_mock():
    with patch("front.main.st.sidebar.title") as mock:
        yield mock

@pytest.fixture
def st_sidebar_success_mock():
    with patch("front.main.st.sidebar.success") as mock:
        yield mock


@pytest.fixture
def st_sidebar_error_mock():
    with patch("front.main.st.sidebar.error") as mock:
        yield mock

@pytest.fixture
def st_sidebar_radio_mock():
    with patch("front.main.st.sidebar.radio") as mock:
        yield mock


@pytest.fixture
def st_radio_mock():
    with patch("front.main.st.radio") as mock:
        yield mock

@pytest.fixture
def st_markdown_mock():
    with patch("front.main.st.markdown") as mock:
        yield mock

@pytest.fixture
def st_error_mock():
    with patch("front.main.st.error") as mock:
        yield mock

@pytest.fixture
def st_success_mock():
    with patch("front.main.st.success") as mock:
        yield mock



@pytest.fixture
def requests_mock():
    with patch("front.main.requests") as mock:
        yield mock

@pytest.fixture
def get_user_by_username_mock():
    with patch("front.main.get_user_by_username") as mock:
        yield mock

@pytest.fixture
def get_group_mock():
    with patch("front.main.get_group") as mock:
        yield mock


@pytest.fixture
def members_display_mock():
    with patch("front.main.members_display") as mock:
        yield mock

@pytest.fixture
def expenses_display_mock():
    with patch("front.main.expenses_display") as mock:
        yield mock


@pytest.fixture
def register_mock():
    with patch("front.main.register") as mock:
        yield mock

@pytest.fixture
def login_mock():
    with patch("front.main.login") as mock:
        yield mock


@pytest.fixture
def st_session_state_mock():
    with patch("front.main.st.session_state") as mock:
        yield mock

@pytest.fixture
def profile_display_mock():
    with patch("front.main.profile_display") as mock:
        yield mock

@pytest.fixture
def groups_display_mock():
    with patch("front.main.groups_display") as mock:
        yield mock

@pytest.fixture
def auth_display_mock():
    with patch("front.main.auth_display") as mock:
        yield mock

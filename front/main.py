import streamlit as st
import requests
import math

# Base URL for the FastAPI server
BASE_URL = "http://localhost:8000"


def register(email, username, password):
    endpoint = f"{BASE_URL}/users"
    response = requests.post(
        endpoint,
        json={"email": email, "username": username, "password": password},
    )
    if response.status_code == 200:
        st.sidebar.success("Registered successfully")
    else:
        st.sidebar.error("Registration failed")


def login(username, password):
    endpoint = f"{BASE_URL}/auth/login"
    response = requests.post(
        endpoint, json={"username": username, "password": password}
    ).json()
    if "status" in response and response["status"] == "success":
        st.sidebar.success("Login successful!")
        st.session_state.logged_in = True
        st.session_state.user_id = response["user_id"]
        st.session_state.username = username
        st.session_state.email = response["email"]
    else:
        st.sidebar.error("Login failed. Invalid username or password.")


def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.email = None
    st.session_state.selected_group = None


def get_user_groups(user_id):
    endpoint = f"{BASE_URL}/users/{user_id}/groups"
    response = requests.get(endpoint)
    return response.json()


def get_user_expenses(user_id):
    endpoint = f"{BASE_URL}/users/{user_id}/expenses"
    response = requests.get(endpoint)
    return response.json()


def get_user_by_username(username):
    endpoint = f"{BASE_URL}/users/username/{username}"
    response = requests.get(endpoint)
    return response.json()


def get_user(user_id):
    endpoint = f"{BASE_URL}/users/{user_id}"
    response = requests.get(endpoint)
    return response.json()


def get_group(group_id):
    endpoint = f"{BASE_URL}/groups/{group_id}"
    response = requests.get(endpoint)
    return response.json()


def get_group_depts(group_id):
    endpoint = f"{BASE_URL}/dept/{group_id}"
    response = requests.get(endpoint)
    return response.json()


def get_user_depts(group_id, user_id):
    endpoint = f"{BASE_URL}/dept/{group_id}/{user_id}"
    response = requests.get(endpoint)
    return response.json()


def add_member(group_id, username):
    user = get_user_by_username(username)
    if "user_id" not in user:
        st.error(f"User {username} doesn't exists")
        return
    endpoint = f"{BASE_URL}/groups/{group_id}/add_member/{user['user_id']}"
    response = requests.post(endpoint).json()
    if "user_id" not in response:
        st.error(f"Couldn't add {username} to the group")
        return
    st.success(f"Added {username} to the group")


def create_expense(group_id, created_by, amount, description):
    if amount <= 0:
        st.error("Amount should be a positive number")
        return
    endpoint = f"{BASE_URL}/expenses"
    response = requests.post(
        endpoint,
        json={
            "group_id": group_id,
            "created_by": created_by,
            "amount": amount,
            "description": description,
        },
    )
    if response.status_code != 200:
        st.error("Couldn't create expense")
        return
    username = st.session_state.username
    st.success(f"Expense with {amount} roubles by {username} was created")


def profile_display():
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.markdown("---")
    st.sidebar.subheader("User Information:")
    st.sidebar.markdown(f"username: **{st.session_state.username}**")
    st.sidebar.markdown(f"email: **{st.session_state.email}**")
    st.sidebar.markdown("---")


def members_display(group):
    st.subheader(f"Total Members: {group['total_members']}")
    username_to_add = st.text_input("Add member", placeholder="username")
    st.button(
        "Add", on_click=lambda: add_member(group["group_id"], username_to_add)
    )
    st.write("<br>", unsafe_allow_html=True)
    st.subheader("Members")
    members = [
        get_user(m["user_id"])["username"] for m in group["groupmembers"]
    ]
    ul_markdown = "\n".join([f"- {item}" for item in members])
    st.write(ul_markdown, unsafe_allow_html=True)


def pay_expense_fn(expense_id, user_id, amount_paid):
    def callback():
        endpoint = f"{BASE_URL}/expenses/participant"
        response = requests.post(
            endpoint,
            json={
                "expense_id": expense_id,
                "user_id": user_id,
                "amount_paid": amount_paid,
            },
        )
        if response.status_code != 200:
            st.error("Couldn't pay expense")
            return {}

        st.success("Paid successfully")
        return {}

    return callback


def pay_dept_fn(amount_paid, dept):
    def callback():
        endpoint = f"{BASE_URL}/dept/{dept['dept_id']}"
        response = requests.patch(
            endpoint,
            json={
                "amount": amount_paid,
            },
        )
        if response.status_code != 200:
            st.error("FAIL")
            return {}

        st.success("OK")
        return {}

    return callback


def delete_expense_fn(expense_id):
    def x():
        endpoint = f"{BASE_URL}/expenses/{expense_id}"
        response = requests.delete(endpoint)
        if response.status_code != 200:
            st.error("Couldn't delete expense")
            return {}

        st.success("Deleted successfully")
        return {}

    return x


def delete_dept_fn(dept):
    def x():
        endpoint = f"{BASE_URL}/dept/{dept['dept_id']}"
        response = requests.delete(endpoint)
        if response.status_code != 200:
            st.error("Couldn't delete dept")
            return {}

        st.success("Deleted successfully")
        return {}

    return x


def name_columns(columns, column_names):
    for i in range(len(column_names)):
        with columns[i]:
            st.text(column_names[i])


def expenses_display(group):
    st.subheader(f"Total expenses: {group['total_expenses']}₽")
    amount = st.number_input("Amount (₽)", placeholder="₽", step=1)
    desc = st.text_input("Description", placeholder="some description")
    st.button(
        "Create",
        on_click=lambda: create_expense(
            group["group_id"], st.session_state.user_id, amount, desc
        ),
        key="expense_create_btn",
    )
    st.write("<br>", unsafe_allow_html=True)
    st.subheader("Expenses")
    name_columns(
        st.columns([0.15, 0.7, 0.15]),
        ["amount", "description", "delete"],
    )
    for e in group["groupexpenses"]:
        st.write("<hr style='margin: 0;'>", unsafe_allow_html=True)
        amount_col, desc_col, del_col = st.columns([0.15, 0.7, 0.15])
        with amount_col:
            st.markdown(f"**{e['amount']}₽**")

        with desc_col:
            st.text(e["description"])

        with del_col:
            st.button(
                "Delete",
                key=f"del_btn_expense_{e['expense_id']}",
                on_click=delete_expense_fn(e["expense_id"]),
            )


def depts_display(group):
    st.subheader("Depts")

    depts = get_group_depts(group["group_id"])

    name_columns(
        st.columns([0.15, 0.25, 0.25, 0.35]),
        ["amount", "debtor", "lender", "payment"],
    )
    for dept in depts:
        st.write("<hr style='margin: 0;'>", unsafe_allow_html=True)
        amount_col, user_col, lender_col, pay_col = st.columns(
            [0.15, 0.25, 0.25, 0.35]
        )

        with amount_col:
            st.markdown(f"**{math.ceil(dept['amount'])}₽**")

        with user_col:
            user = get_user(dept["user_id"])
            st.text(user["username"])

        with lender_col:
            lender = get_user(dept["lender_id"])
            st.text(lender["username"])

        with pay_col:
            input_col, btn_col = st.columns(2)
            with input_col:
                amount_paid = st.number_input(
                    "Amount (₽)",
                    step=1,
                    key=f"user_{dept['user_id']}_lender_{dept['lender_id']}",
                    placeholder="₽",
                )
            with btn_col:
                st.button(
                    "Pay",
                    key=f"pay_btn_expense_user_{dept['user_id']}_lender_{dept['lender_id']}",
                    on_click=pay_dept_fn(amount_paid, dept),
                )


def a_group_display(group):
    group = get_group(group["group_id"])
    st.title(group["group_name"])

    mode = st.radio(
        "Group Navigation",
        ("Members", "Expenses", "Depts"),
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("---")
    if mode == "Members":
        members_display(group)
    if mode == "Expenses":
        expenses_display(group)
    if mode == "Depts":
        depts_display(group)


def groups_display():
    groups = get_user_groups(st.session_state.user_id)
    group_names = [g["group_name"] for g in groups]
    group_name = st.sidebar.selectbox(
        "Groups", group_names, placeholder="Choose a Group"
    )
    for g in groups:
        if g["group_name"] == group_name:
            a_group_display(g)

    st.sidebar.markdown("---")
    group_name = st.sidebar.text_input("Create", placeholder="New Group Name")
    st.sidebar.button(
        "Create",
        on_click=lambda: create_group(group_name, st.session_state.user_id),
        key="group_create_btn",
    )


def create_group(group_name, created_by):
    endpoint = f"{BASE_URL}/groups/"
    data = {"group_name": group_name, "created_by": created_by}
    response = requests.post(endpoint, json=data)
    return response.json()


def auth_display():
    st.title("Lazy Split")
    st.subheader("Please login to use the app")

    mode = st.sidebar.radio(
        "Auth Form",
        ("Login", "Register"),
        horizontal=True,
        label_visibility="hidden",
    )
    if mode == "Register":
        st.sidebar.title("Registration")
        email = st.sidebar.text_input("Email")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        st.sidebar.button(
            "Register", on_click=lambda: register(email, username, password)
        )
    elif mode == "Login":
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        st.sidebar.button("Login", on_click=lambda: login(username, password))


def main():
    if st.session_state.get("logged_in"):
        profile_display()
        groups_display()
    else:
        auth_display()


if __name__ == "__main__":
    main()

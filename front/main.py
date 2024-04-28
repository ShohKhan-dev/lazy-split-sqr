from click import group
from numpy import outer
import streamlit as st
import requests
import time

# Base URL for the FastAPI server
BASE_URL = "http://localhost:8000"

def register(email, username, password):
    endpoint = f"{BASE_URL}/users"
    response = requests.post(endpoint, json={"email":email, "username": username, "password": password}).json()
    if "user_id" in response:
        st.sidebar.success("Registered successfully")
    else:
        st.sidebar.error("Registration failed")

def login(username, password):
    endpoint = f"{BASE_URL}/auth/login"
    response = requests.post(endpoint, json={"username": username, "password": password}).json()
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
        st.error(f"Amount should be a positive number")
        return
    endpoint = f"{BASE_URL}/expenses"
    response = requests.post(endpoint, json={"group_id": group_id, "created_by":created_by, "amount": amount, "description":description}).json()
    # if "created_at" not in response:
    #     st.error(f"Couldn't create expense")
    #     return
    # st.success(f"Expense with {amount} roubles by {st.session_state.username} was created")

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
    st.button("Add", on_click=lambda:add_member(group['group_id'], username_to_add))
    st.markdown("---")
    members = [get_user(m['user_id'])['username'] for m in group['groupmembers']]
    ul_markdown = "\n".join([f"- {item}" for item in members])
    st.write(ul_markdown, unsafe_allow_html=True)
        

def expenses_display(group):
    st.subheader(f"Total expenses: {group['total_expenses']}")
    amount = st.number_input("Amount", placeholder="roubles", step=1)
    desc = st.text_input("Description", placeholder="some description")
    st.button("Create", on_click=lambda:create_expense(group["group_id"], st.session_state.user_id, amount, desc), key="expense_create_btn")
    st.markdown("---")
    expenses = [f"**{e['amount']}₽** ---- {e['description']}" for e in group['groupexpenses']]
    ul_markdown = "\n".join([f"- {item}" for item in expenses])
    st.write(ul_markdown, unsafe_allow_html=True)

def a_group_display(group):
    group = get_group(group["group_id"])
    st.title(group["group_name"])

    mode = st.radio("", ("Members", "Expenses"), horizontal=True)
    st.markdown("---")
    if mode == "Members":
        members_display(group)
    if mode == "Expenses":
        expenses_display(group)


def groups_display():
    groups = get_user_groups(st.session_state.user_id)
    group_names = [g["group_name"] for g in groups]
    group_name = st.sidebar.selectbox("Groups", group_names, placeholder="Choose a Group")
    for g in groups:
        if g["group_name"] == group_name:
            a_group_display(g)
            
    st.sidebar.markdown("---")
    group_name = st.sidebar.text_input("Create", placeholder="New Group Name")
    st.sidebar.button("Create", on_click=lambda:create_group(group_name, st.session_state.user_id), key="group_create_btn")


def create_group(group_name, created_by):
    endpoint = f"{BASE_URL}/groups/"
    data = {"group_name": group_name, "created_by": created_by}
    response = requests.post(endpoint, json=data)
    return response.json()


def auth_display():
    st.title("Lazy Split")
    st.subheader("Please login to use the app")

    mode = st.sidebar.radio("", ("Login", "Register"), horizontal=True)
    if mode == "Register":
        st.sidebar.title("Registration")
        email = st.sidebar.text_input("Email")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        st.sidebar.button("Register", on_click=lambda:register(email, username, password))
    elif mode == "Login":
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        st.sidebar.button("Login", on_click=lambda:login(username, password))


# Streamlit UI
def main():
    if st.session_state.get("logged_in"):
        profile_display()
        groups_display()
    else:
        auth_display()

if __name__ == "__main__":
    main()

from click import group
from numpy import outer
import streamlit as st
import requests
import time

# Base URL for the FastAPI server
BASE_URL = "http://localhost:8000"

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
    endpoint = f"{BASE_URL}/users/{username}"
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


def profile_display():
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.markdown("---")
    st.sidebar.subheader("User Information:")
    st.sidebar.markdown(f"username: **{st.session_state.username}**")
    st.sidebar.markdown(f"email: **{st.session_state.email}**")
    st.sidebar.markdown("---")
    
def a_group_display(group):
    st.title(group["group_name"])
    st.markdown("---")
    st.subheader(f"Total expenses: {group['total_expenses']}")
    st.subheader(f"Total Members: {group['total_members']}")
    st.markdown("---")
    username_to_add = st.text_input("Add member", placeholder="username")
    st.button("Add", on_click=lambda:add_member(group['group_id'], username_to_add))
    
def groups_display():
    groups = get_user_groups(st.session_state.user_id)
    group_names = [g["group_name"] for g in groups]
    group_name = st.sidebar.selectbox("Groups", group_names, placeholder="Choose a Group")
    for g in groups:
        if g["group_name"] == group_name:
            a_group_display(g)
            
    st.sidebar.markdown("---")
    group_name = st.sidebar.text_input("Create", placeholder="New Group Name")
    st.sidebar.button("Create", on_click=lambda:create_group(group_name, st.session_state.user_id))


def create_group(group_name, created_by):
    endpoint = f"{BASE_URL}/groups/"
    data = {"group_name": group_name, "created_by": created_by}
    response = requests.post(endpoint, json=data)
    return response.json()


# Streamlit UI
def main():
    if st.session_state.get("logged_in"):
        profile_display()
        groups_display()

    else :
        st.title("Lazy Split")
        st.subheader("Please login to use the app")
        st.sidebar.title("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        st.sidebar.button("Login", on_click=lambda:login(username, password))

if __name__ == "__main__":
    main()
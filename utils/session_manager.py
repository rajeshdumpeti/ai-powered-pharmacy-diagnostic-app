# utils/session_manager.py
import streamlit as st
import json
import os

SESSION_FILE = "data/session_state.json" # Ensure this path is correct

def load_session_state_manual():
    """Loads session state (username, logged_in status, user_role) from a JSON file."""
    if not os.path.exists("data"):
        os.makedirs("data")
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                persisted_state = json.load(f)
            # Load only the critical session state variables
            if "logged_in" in persisted_state:
                st.session_state.logged_in = persisted_state["logged_in"]
            if "username" in persisted_state:
                st.session_state.username = persisted_state["username"]
            if "user_role" in persisted_state: # NEW: Load user_role
                st.session_state.user_role = persisted_state["user_role"]
            st.success("Session loaded --- will be removed before deplying to Prod.") # Optional: for debugging
        except (json.JSONDecodeError, KeyError) as e:
            st.error(f"Error loading session state: {e}. Starting fresh.")
            # Ensure session state is reset if file is corrupted/missing keys
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_role = "" # Reset role on error
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE) # Remove corrupted file
    else:
        # If file doesn't exist, ensure session state is initialized to default (not logged in)
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'username' not in st.session_state:
            st.session_state.username = ""
        if 'user_role' not in st.session_state:
            st.session_state.user_role = ""


def save_session_state_manual():
    """Saves critical session state (username, logged_in status, user_role) to a JSON file."""
    persisted_state = {
        "logged_in": st.session_state.get("logged_in", False),
        "username": st.session_state.get("username", ""),
        "user_role": st.session_state.get("user_role", "") # NEW: Save user_role
    }
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(SESSION_FILE, "w") as f:
        json.dump(persisted_state, f)
    # st.info("Session saved.") # Optional: for debugging
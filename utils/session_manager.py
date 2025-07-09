import streamlit as st
import json
import os

SESSION_STATE_FILE = "user_session_state.json"

def load_session_state_manual():
    """
    Loads specific session state variables from a JSON file, but NOT login status.
    This is for consistency, but login status will default to False.
    """
    if os.path.exists(SESSION_STATE_FILE):
        try:
            with open(SESSION_STATE_FILE, "r") as f:
                loaded_state = json.load(f)
            if "username" in loaded_state:
                st.session_state.username = loaded_state["username"]
        except json.JSONDecodeError:
            st.warning("Corrupted session state file found. Starting fresh.")
        except Exception as e:
            st.error(f"Error loading session state: {e}. Starting fresh.")

def save_session_state_manual():
    """Saves specific session state variables to a JSON file."""
    state_to_save = {
        "username": st.session_state.get("username", "")
    }
    try:
        with open(SESSION_STATE_FILE, "w") as f:
            json.dump(state_to_save, f)
    except Exception as e:
        st.error(f"Error saving session state: {e}")
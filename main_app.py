# main_app.py
import streamlit as st
from datetime import date
import json
import os

# Import services
from services.database_service import init_db
from services.auth_service import verify_user, add_user
from utils.session_manager import load_session_state_manual, save_session_state_manual
from utils.styles import apply_custom_styles

# Import page functions
from pages.quick_drug_search_page import show_quick_drug_search_page
from pages.add_drug_page import show_add_drug_page
from pages.add_diagnostic_page import show_add_diagnostic_page
from pages.delete_record_page import show_delete_record_page
from pages.patient_summary_page import show_patient_summary_page
from pages.inventory_insights_page import show_inventory_insights_page
from pages.custom_report_page import show_custom_report_page
from pages.natural_language_query_page import show_natural_language_query_page
from pages.chatbot_page import show_chatbot_page
from pages.image_analysis_page import show_image_analysis_page
from pages.dashboard_page import show_dashboard_page # Add this line


# Call init_db at the beginning of the script to ensure tables and data exist
init_db()


# --- Streamlit APP Configuration ---
st.set_page_config(page_title="Rajesh's | Pharmacy & Diagnostics SQL Assistant", page_icon="⚕️", layout="wide")

st.markdown("<h1 style='text-align: center; color: #008080;'>Rajesh's Gemini App</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #2F4F4F;'>Your AI-Powered <b>Pharmacy & Diagnostics SQL Assistant</b></h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #696969;'>Comprehensive tool for managing pharmacy inventory and patient diagnostic data.</p>", unsafe_allow_html=True)

# Apply custom CSS
apply_custom_styles()


# --- Session State Initialization ---
# Initialize logged_in and username first, then load username from file
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

load_session_state_manual() # This will only load 'username' if available

# Initialize other session states for pages
if 'search_input' not in st.session_state:
    st.session_state.search_input = ""
if 'selected_drug_for_details' not in st.session_state:
    st.session_state.selected_drug_for_details = ""
if 'question_input_value' not in st.session_state:
    st.session_state.question_input_value = ""
if 'prompt_history' not in st.session_state:
    st.session_state.prompt_history = []
if 'trigger_submit_llm' not in st.session_state:
    st.session_state.trigger_submit_llm = False
if 'chatbot_history' not in st.session_state:
    st.session_state.chatbot_history = []
# Image analysis specific session states
if 'uploaded_image_data' not in st.session_state:
    st.session_state.uploaded_image_data = None
if 'image_analysis_result' not in st.session_state:
    st.session_state.image_analysis_result = ""
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = ""
if 'uploaded_file_size' not in st.session_state:
    st.session_state.uploaded_file_size = ""


# NEW: Session state for page navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = "login" # Default to login page


# --- Authentication Logic (Modern UI) ---
def login_form_ui():
    st.markdown("<h4 style='text-align: center; color: #008080;'>Login to your account</h4>", unsafe_allow_html=True)
    with st.form("login_form"):
        username_default = st.session_state.get("username", "")
        username = st.text_input("Username", key="login_username_ui", value=username_default)
        password = st.text_input("Password", type="password", key="login_password_ui")
        login_button = st.form_submit_button("Login", help="Click to log in")

        if login_button:
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                save_session_state_manual()
                st.success(f"Logged in as {username}!")
                st.session_state.current_page = "dashboard"
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")

def signup_form_ui():
    st.markdown("<h4 style='text-align: center; color: #008080;'>Create a new account</h4>", unsafe_allow_html=True)
    with st.form("signup_form"):
        new_username = st.text_input("Choose Username", key="signup_username_ui")
        new_password = st.text_input("Choose Password", type="password", key="signup_password_ui")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password_ui")
        signup_button = st.form_submit_button("Sign Up", help="Click to create a new account")

        if signup_button:
            if not new_username or not new_password or not confirm_password:
                st.error("All fields are required. Please fill them out.")
            elif new_password != confirm_password:
                st.error("Passwords do not match. Please re-enter them.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                if add_user(new_username, new_password):
                    st.success(f"Account '{new_username}' created successfully! You can now log in.")
                    st.session_state.username = new_username
                    save_session_state_manual()
                    st.session_state.logged_in = False
                    st.session_state.current_page = "login" # Stay on login page after signup
                    st.rerun()


# --- Main App Logic (Conditional based on login status and current_page) ---

# This handles rendering different "pages"
if st.session_state.logged_in:
    # Sidebar for navigation
    st.sidebar.markdown(f"Welcome, **{st.session_state.username}**!", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Features")

    # Navigation buttons
    if st.sidebar.button("Dashboard", key="nav_dashboard"):
        st.session_state.current_page = "dashboard"
        st.rerun()
    if st.sidebar.button("Quick Drug Search", key="nav_quick_drug_search"):
        st.session_state.current_page = "quick_drug_search"
        st.rerun()
    if st.sidebar.button("Add New Drug", key="nav_add_drug"):
        st.session_state.current_page = "add_drug"
        st.rerun()
    if st.sidebar.button("Add Diagnostic Record", key="nav_add_diagnostic_record"):
        st.session_state.current_page = "add_diagnostic_record"
        st.rerun()
    if st.sidebar.button("Delete Record by ID", key="nav_delete_record"):
        st.session_state.current_page = "delete_record"
        st.rerun()
    if st.sidebar.button("Patient History Summarizer", key="nav_patient_summary"):
        st.session_state.current_page = "patient_summary"
        st.rerun()
    if st.sidebar.button("Inventory Insights", key="nav_inventory_insights"):
        st.session_state.current_page = "inventory_insights"
        st.rerun()
    if st.sidebar.button("Custom Data Report", key="nav_custom_report"):
        st.session_state.current_page = "custom_report"
        st.rerun()
    if st.sidebar.button("Natural Language Query (Advanced)", key="nav_natural_language_query"):
        st.session_state.current_page = "natural_language_query"
        st.rerun()
    if st.sidebar.button("AI Chatbot for DB Info", key="nav_chatbot"):
        st.session_state.current_page = "chatbot"
        st.rerun()
    if st.sidebar.button("Medical Image Analysis", key="nav_image_analysis"):
        st.session_state.current_page = "image_analysis"
        st.rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout", key="logout_btn_sidebar"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        save_session_state_manual()
        # Clear all functional session states on logout
        st.session_state.prompt_history = []
        st.session_state.search_input = ""
        st.session_state.selected_drug_for_details = ""
        st.session_state.question_input_value = ""
        st.session_state.trigger_submit_llm = False
        st.session_state.chatbot_history = []
        # Clear image analysis state too
        st.session_state.uploaded_image_data = None
        st.session_state.image_analysis_result = ""
        st.session_state.uploaded_file_name = ""
        st.session_state.uploaded_file_size = ""
        
        st.session_state.current_page = "login" # Go back to login page on logout
        st.rerun()

    # Conditional rendering based on current_page
    if st.session_state.current_page == "dashboard": # Add this condition
        show_dashboard_page()
    elif st.session_state.current_page == "quick_drug_search":
        show_quick_drug_search_page()
    elif st.session_state.current_page == "add_drug":
        show_add_drug_page()
    elif st.session_state.current_page == "add_diagnostic_record":
        show_add_diagnostic_page()
    elif st.session_state.current_page == "delete_record":
        show_delete_record_page()
    elif st.session_state.current_page == "patient_summary":
        show_patient_summary_page()
    elif st.session_state.current_page == "inventory_insights":
        show_inventory_insights_page()
    elif st.session_state.current_page == "custom_report":
        show_custom_report_page()
    elif st.session_state.current_page == "natural_language_query":
        show_natural_language_query_page()
    elif st.session_state.current_page == "chatbot":
        show_chatbot_page()
    elif st.session_state.current_page == "image_analysis":
        show_image_analysis_page()
    else: 
        st.session_state.current_page = "dashboard" 
        st.rerun()

else: # Not logged in, show login/signup
    st.session_state.current_page = "login" # Ensure page is set to login if not logged in
    st.markdown("<br>", unsafe_allow_html=True)
    auth_container = st.container()
    with auth_container:
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            st.markdown("<div style='background-color:#F5F5F5; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 8px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

            auth_choice = st.radio(
                "Already have an account or need to create one?",
                ("Login", "Sign Up"),
                index=0,
                key="auth_choice_radio",
                horizontal=True
            )
            st.markdown("---")

            if auth_choice == "Login":
                login_form_ui()
            else:
                signup_form_ui()

            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
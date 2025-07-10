# main_app.py
import streamlit as st
from datetime import date
import json
import os
import random
import smtplib
from email.mime.text import MIMEText

# Import services
from services.database_service import init_db
from services.auth_service import verify_user, add_user, get_user_role, store_otp, verify_otp
from utils.session_manager import load_session_state_manual, save_session_state_manual
from utils.styles import apply_custom_styles

# Import page functions
from pages.dashboard_page import show_dashboard_page
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
from pages.billing_invoice_page import show_billing_page


# Initialize DB
init_db()

# Streamlit config
st.set_page_config(page_title="Rajesh's | Pharmacy & Diagnostics SQL Assistant", page_icon="⚕️", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

apply_custom_styles()

# Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""
if 'otp_verified' not in st.session_state:
    st.session_state.otp_verified = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "login"
    
# Ensure all required session state keys are initialized
default_session_keys = {
    "search_input": "",
    "selected_drug_for_details": "",
    "question_input_value": "",
    "chatbot_history": [],
    "trigger_submit_llm": False,
    "uploaded_image_data": None,
    "image_analysis_result": "",
    "uploaded_file_name": "",
    "uploaded_file_size": ""
}

for key, default_value in default_session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

load_session_state_manual()


# OTP email sending function (mocked for local)
def send_otp_email(username, otp):
    print(f"OTP for {username}: {otp} (mocked for local testing)")

# Auth UI

def login_form_ui():
    st.markdown("<h4 style='text-align: center; color: #008080;'>Login to your account</h4>", unsafe_allow_html=True)
    
    if not st.session_state.get("otp_pending"):
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username_ui")
            password = st.text_input("Password", type="password", key="login_password_ui")
            login_button = st.form_submit_button("Login")

            if login_button:
                if verify_user(username, password):
                    otp = str(random.randint(100000, 999999))
                    st.session_state["otp_code"] = otp  # Store OTP in session
                    st.session_state["otp_username"] = username  # Save username temporarily
                    st.session_state["otp_user_role"] = get_user_role(username)
                    send_otp_email(username, otp)
                    st.session_state.otp_pending = True
                    st.success("OTP sent to registered email (mocked). Please enter below.")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    else:
        with st.form("otp_form"):
            otp_input = st.text_input("Enter OTP", key="otp_input_ui")
            otp_login_btn = st.form_submit_button("Login with OTP")

            if otp_login_btn:
                expected_otp = st.session_state.get("otp_code")
                if otp_input == expected_otp:
                    st.success("✅ OTP verified successfully!")
                    st.session_state.logged_in = True
                    st.session_state.username = st.session_state.get("otp_username")
                    st.session_state.user_role = st.session_state.get("otp_user_role")
                    st.session_state.otp_pending = False
                    st.session_state.otp_code = ""  # clear OTP
                    st.session_state.current_page = "dashboard"
                    save_session_state_manual()
                    st.rerun()
                else:
                    st.error("❌ Invalid OTP. Please try again.")
def signup_form_ui():
    st.markdown("<h4 style='text-align: center; color: #008080;'>Create a New Account</h4>", unsafe_allow_html=True)
    with st.form("signup_form"):
        new_username = st.text_input("Choose a Username", key="signup_username_ui")
        new_password = st.text_input("Create Password", type="password", key="signup_password_ui")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password_ui")
        role_options = ["Pharmacist", "Doctor", "Admin"]
        selected_role = st.selectbox("Select Your Role", role_options, key="signup_role_ui")
        signup_button = st.form_submit_button("Sign Up")

        if signup_button:
            if not new_username or not new_password or not confirm_password:
                st.warning("Please fill in all fields.")
            elif new_password != confirm_password:
                st.warning("Passwords do not match.")
            elif len(new_password) < 6:
                st.warning("Password must be at least 6 characters.")
            else:
                success = add_user(new_username, new_password, selected_role)
                if success:
                    st.success(f"Account created successfully as {selected_role}! Please log in.")
                else:
                    st.error("Username already exists. Please try another.")

# Auth Routing
if not st.session_state.logged_in:
    st.markdown("<br>", unsafe_allow_html=True)
    auth_container = st.container()
    with auth_container:
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            auth_choice = st.radio("", ("Login", "Sign Up"), key="auth_choice_radio", horizontal=True)
            st.markdown("---")
            if auth_choice == "Login":
                login_form_ui()
            else:
                signup_form_ui()
    st.stop()

# Sidebar Navigation Based on Role
with st.sidebar:
    st.markdown(f"**Logged in as:** `{st.session_state.username}`")
    st.markdown(f"**Role:** `{st.session_state.user_role}`")
    st.markdown("---")

    role = st.session_state.user_role

    if role == "Admin" or role == "Doctor":
        if st.button("Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()

    if role in ["Admin", "Pharmacist"]:
        if st.button("Quick Drug Search"):
            st.session_state.current_page = "quick_drug_search"
            st.rerun()
        if st.button("Add New Drug"):
            st.session_state.current_page = "add_drug"
            st.rerun()
        if st.button("Inventory Insights"):
            st.session_state.current_page = "inventory_insights"
            st.rerun()
        if st.button("Custom Data Report"):
            st.session_state.current_page = "custom_report"
            st.rerun()
        if st.button("Billing & Invoicing"):
            st.session_state.current_page = "billing"
            st.rerun()

    if role in ["Admin", "Doctor"]:
        if st.button("Add Diagnostic Record"):
            st.session_state.current_page = "add_diagnostic_record"
            st.rerun()
        if st.button("Patient Summary"):
            st.session_state.current_page = "patient_summary"
            st.rerun()
        if st.button("AI Chatbot"):
            st.session_state.current_page = "chatbot"
            st.rerun()
        if st.button("Medical Image Analysis"):
            st.session_state.current_page = "image_analysis"
            st.rerun()

    if role in ["Admin", "Doctor"]:
        if st.button("Delete Record"):
            st.session_state.current_page = "delete_record"
            st.rerun()

    if role in ["Admin", "Pharmacist", "Doctor"]:
        if st.button("Natural Language Query"):
            st.session_state.current_page = "natural_language_query"
            st.rerun()

    if st.button("Logout", type="primary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_role = ""
        st.session_state.otp_verified = False
        st.session_state.current_page = "login"
        st.rerun()

# Render Pages
page = st.session_state.current_page
if page == "dashboard":
    show_dashboard_page()
elif page == "quick_drug_search":
    show_quick_drug_search_page()
elif page == "add_drug":
    show_add_drug_page()
elif page == "add_diagnostic_record":
    show_add_diagnostic_page()
elif page == "delete_record":
    show_delete_record_page()
elif page == "patient_summary":
    show_patient_summary_page()
elif page == "inventory_insights":
    show_inventory_insights_page()
elif page == "custom_report":
    show_custom_report_page()
elif page == "natural_language_query":
    show_natural_language_query_page()
elif page == "chatbot":
    show_chatbot_page()
elif page == "image_analysis":
    show_image_analysis_page()
elif page == "billing":
    show_billing_page()
else:
    show_dashboard_page()

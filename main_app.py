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
from services.billing_service import init_invoice_db
from services.auth_service import verify_user, add_user, get_user_role 

# Import utility functions
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
init_invoice_db()

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


# --- Session State Initialization and Loading ---

# Initialize all session state variables with default values first
# These defaults will be overwritten by load_session_state_manual if a session file exists
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_role' not in st.session_state:
    st.session_state.user_role = ""
if 'otp_verified' not in st.session_state: # This might be less critical for persistence across refreshes
    st.session_state.otp_verified = False
if 'otp_pending' not in st.session_state: # Initialize otp_pending
    st.session_state.otp_pending = False
if 'otp_code' not in st.session_state: # Initialize otp_code
    st.session_state.otp_code = ""
if 'otp_username' not in st.session_state: # Initialize otp_username
    st.session_state.otp_username = ""
if 'otp_user_role' not in st.session_state: # Initialize otp_user_role
    st.session_state.otp_user_role = ""

# Load session state from file immediately after basic initialization
load_session_state_manual()

# Initialize other page-specific session states if they don't exist
# Crucially, these should only be set if not already loaded by load_session_state_manual
default_session_keys = {
    "search_input": "",
    "selected_drug_for_details": "",
    "question_input_value": "",
    "chatbot_history": [],
    "trigger_submit_llm": False,
    "uploaded_image_data": None,
    "image_analysis_result": "",
    "uploaded_file_name": "",
    "uploaded_file_size": "",
    "invoice_items": [],
    "invoice_patient_name": "",
    "invoice_payment_mode": "Cash",
    "current_page": "dashboard" if st.session_state.logged_in else "login" # Set initial page based on login status
}

for key, default_value in default_session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


# OTP email sending function (mocked for local)
def send_otp_email(username, otp):
    # In a real application, replace this with actual email sending logic
    # using smtplib or a third-party email service.
    # For local testing, this print statement is sufficient.
    print(f"--- MOCKED OTP EMAIL ---")
    print(f"To: {username}'s Registered Email") # Assuming username is tied to an email
    print(f"Subject: Your OTP for Gemini App Login")
    print(f"Your One-Time Password (OTP) is: {otp}")
    print(f"-------------------------------------------------------------------------------")
    # Example for actual email (requires sender_email, sender_password, and user's actual email)
    # try:
    #     sender_email = os.environ.get("SENDER_EMAIL")
    #     sender_password = os.environ.get("SENDER_PASSWORD") # Use app-specific password if using Gmail
    #     receiver_email = "user_email_from_db_or_auth_service(username)" # You'd need to fetch the user's email
    #     if not sender_email or not sender_password or not receiver_email:
    #         print("Email configuration missing for actual OTP sending.")
    #         return

    #     msg = MIMEText(f"Your One-Time Password (OTP) is: {otp}")
    #     msg['Subject'] = "Your OTP for Gemini App Login"
    #     msg['From'] = sender_email
    #     msg['To'] = receiver_email

    #     with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    #         smtp.login(sender_email, sender_password)
    #         smtp.send_message(msg)
    #     print(f"OTP email sent to {receiver_email}")
    # except Exception as e:
    #     print(f"Failed to send OTP email: {e}")
    pass


# Auth UI
def login_form_ui():
    st.markdown("<h4 style='text-align: center; color: #FFFF;'>Login to your account</h4>", unsafe_allow_html=True)

    if not st.session_state.get("otp_pending"):
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username_ui", value=st.session_state.get("otp_username", "")) # Pre-fill if coming from OTP resend
            password = st.text_input("Password", type="password", key="login_password_ui")
            login_button = st.form_submit_button("Login")

            if login_button:
                if verify_user(username, password):
                    otp = str(random.randint(100000, 999999))
                    st.session_state["otp_code"] = otp
                    st.session_state["otp_username"] = username
                    st.session_state["otp_user_role"] = get_user_role(username) # Get role after successful verification
                    send_otp_email(username, otp)
                    st.session_state.otp_pending = True
                    st.success(f"OTP sent to registered email for {username} (mocked). Please enter below.")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    else: # OTP is pending
        st.info(f"An OTP has been sent to {st.session_state.get('otp_username', 'your email')} (mocked).")
        with st.form("otp_form"):
            otp_input = st.text_input("Enter OTP", key="otp_input_ui")
            col_otp_btns = st.columns(2)
            with col_otp_btns[0]:
                otp_login_btn = st.form_submit_button("Login with OTP")
            with col_otp_btns[1]:
                resend_otp_btn = st.form_submit_button("Resend OTP")

            if otp_login_btn:
                expected_otp = st.session_state.get("otp_code")
                if otp_input == expected_otp:
                    st.success("✅ OTP verified successfully!")
                    st.session_state.logged_in = True
                    st.session_state.username = st.session_state.get("otp_username")
                    st.session_state.user_role = st.session_state.get("otp_user_role")
                    st.session_state.otp_pending = False
                    st.session_state.otp_code = ""  # clear OTP
                    st.session_state.current_page = "dashboard" # Navigate to dashboard
                    save_session_state_manual() # Save persisted session state after successful login
                    st.rerun()
                else:
                    st.error("❌ Invalid OTP. Please try again.")
            elif resend_otp_btn:
                # Resend OTP
                username_to_resend = st.session_state.get("otp_username")
                if username_to_resend:
                    otp = str(random.randint(100000, 999999))
                    st.session_state["otp_code"] = otp
                    send_otp_email(username_to_resend, otp)
                    st.info(f"New OTP sent to {username_to_resend} (mocked).")
                    st.rerun() # Rerun to update the message
                else:
                    st.error("Cannot resend OTP. Please go back to login and try again.")
                    st.session_state.otp_pending = False # Reset state
                    st.rerun()


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
                    st.session_state.otp_username = new_username # Pre-fill username on login form
                    st.session_state.current_page = "login" # Redirect to login page
                    st.rerun()
                else:
                    st.error("Username already exists. Please try another.")


# Auth Routing: This block handles login/signup and stops execution if not logged in.
if not st.session_state.logged_in:
    # Ensure current_page is always "login" when not logged in, but don't rerender immediately
    # if already on the login page to avoid infinite loops during form submissions.
    if st.session_state.current_page != "login":
        st.session_state.current_page = "login"
        # st.rerun() # Removed st.rerun here to prevent issues with form submission on login page itself

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
    st.stop() # This stops the execution of the script if not logged in, preventing sidebar from rendering.

# Sidebar Navigation Based on Role: This block only executes if st.session_state.logged_in is True
with st.sidebar:
    st.markdown(f"**Logged in as:** `{st.session_state.username}`")
    st.markdown(f"**Role:** `{st.session_state.user_role}`")
    st.markdown("---")

    role = st.session_state.user_role

    # Admin and Doctor can see Dashboard
    if role in ["Admin", "Doctor"]:
        if st.button("Dashboard", key="nav_dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()

    # Admin and Pharmacist roles for drug/inventory related pages
    if role in ["Admin", "Pharmacist"]:
        if st.button("Quick Drug Search", key="nav_quick_drug_search"):
            st.session_state.current_page = "quick_drug_search"
            st.rerun()
        if st.button("Add New Drug", key="nav_add_drug"):
            st.session_state.current_page = "add_drug"
            st.rerun()
        if st.button("Inventory Insights", key="nav_inventory_insights"):
            st.session_state.current_page = "inventory_insights"
            st.rerun()
        if st.button("Custom Data Report", key="nav_custom_report"):
            st.session_state.current_page = "custom_report"
            st.rerun()
        if st.button("Checkout / Billing"):
            st.session_state.current_page = "billing"
            st.rerun()

    # Admin and Doctor roles for diagnostic, patient summary, AI chatbot, image analysis
    if role in ["Admin", "Doctor"]:
        if st.button("Add Diagnostic Record", key="nav_add_diagnostic_record"):
            st.session_state.current_page = "add_diagnostic_record"
            st.rerun()
        if st.button("Patient Summary", key="nav_patient_summary"):
            st.session_state.current_page = "patient_summary"
            st.rerun()
        if st.button("AI Chatbot", key="nav_chatbot"):
            st.session_state.current_page = "chatbot"
            st.rerun()
        if st.button("Medical Image Analysis", key="nav_image_analysis"):
            st.session_state.current_page = "image_analysis"
            st.rerun()

    # Admin and Doctor for Delete Record
    if role in ["Admin", "Doctor"]:
        if st.button("Delete Record", key="nav_delete_record"):
            st.session_state.current_page = "delete_record"
            st.rerun()

    # All roles for Natural Language Query
    if role in ["Admin", "Pharmacist", "Doctor"]:
        if st.button("Natural Language Query", key="nav_natural_language_query"):
            st.session_state.current_page = "natural_language_query"
            st.rerun()

    # Logout button, always visible when logged in
    st.markdown("---")
    if st.button("Logout", type="primary", key="logout_sidebar"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_role = ""
        st.session_state.otp_verified = False
        st.session_state.otp_pending = False
        st.session_state.otp_code = ""
        st.session_state.current_page = "login"
        # Clear all functional session states on logout for a clean restart
        st.session_state.search_input = ""
        st.session_state.selected_drug_for_details = ""
        st.session_state.question_input_value = ""
        st.session_state.chatbot_history = []
        st.session_state.trigger_submit_llm = False
        st.session_state.uploaded_image_data = None
        st.session_state.image_analysis_result = ""
        st.session_state.uploaded_file_name = ""
        st.session_state.uploaded_file_size = ""
        st.session_state.invoice_items = []
        st.session_state.invoice_patient_name = ""
        st.session_state.invoice_payment_mode = "Cash"
        save_session_state_manual() # Save cleared session state (logged_out = False)
        st.rerun()


# Render Pages based on current_page session state
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
# Note: Natural Language Query is only if it's not a sensitive admin feature
elif page == "natural_language_query":
    show_natural_language_query_page()
elif page == "chatbot":
    show_chatbot_page()
elif page == "image_analysis":
    show_image_analysis_page()
elif page == "billing":
    show_billing_page()
else:
    # Fallback for unexpected current_page values when logged in
    # This ensures a valid page is always shown after login.
    st.session_state.current_page = "dashboard"
    st.rerun() # Rerun to show the dashboard if it was an invalid page
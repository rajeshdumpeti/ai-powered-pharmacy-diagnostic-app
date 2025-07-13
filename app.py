# app.py
import streamlit as st
from datetime import date # Added for forms

# Import functions from your modules
from database_ops import init_db, execute_sql_query, add_user, verify_user
from gemini_client import get_gemini_response
from prompts import LLM_PROMPT

# Call init_db at the beginning of the script to ensure tables and data exist
init_db()


# --- Streamlit APP Configuration ---
st.set_page_config(page_title="Rajesh's | Pharmacy & Diagnostics SQL Assistant", page_icon="⚕️", layout="wide")

st.markdown("<h1 style='text-align: center; color: #008080;'>Rajesh's Gemini App</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #2F4F4F;'>Your AI-Powered <b>Pharmacy & Diagnostics SQL Assistant</b></h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #696969;'>Comprehensive tool for managing pharmacy inventory and patient diagnostic data.</p>", unsafe_allow_html=True)


# --- Session State Initialization for Authentication ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
# Existing session state initializations
if 'search_input' not in st.session_state:
    st.session_state.search_input = ""
if 'selected_drug_for_details' not in st.session_state:
    st.session_state.selected_drug_for_details = ""
if 'question_input_value' not in st.session_state:
    st.session_state.question_input_value = ""
if 'prompt_history' not in st.session_state:
    st.session_state.prompt_history = []


# --- Authentication Logic ---
def login_form_ui():
    st.markdown("<h4 style='text-align: center; color: #008080;'>Login to your account</h4>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username_ui")
        password = st.text_input("Password", type="password", key="login_password_ui")
        login_button = st.form_submit_button("Login", help="Click to log in")

        if login_button:
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Logged in as {username}!")
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
                    # Optionally, log them in immediately:
                    # st.session_state.logged_in = True
                    # st.session_state.username = new_username
                    # st.rerun()
                # Error messages for username exists or db error handled by add_user function

# --- Display Login/Signup UI or Main App ---
if not st.session_state.logged_in:
    st.markdown("<br>", unsafe_allow_html=True) # Add some space

    # Centered container for auth forms
    auth_container = st.container()
    with auth_container:
        col_left, col_center, col_right = st.columns([1, 2, 1]) # Use columns to center content
        with col_center:
            # st.markdown("<div style='background-color:#F5F5F5; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 8px rgba(0,0,0,0.1);'>", unsafe_allow_html=True)
            
            auth_choice = st.radio(
                "Already have an account or need to create one?",
                ("Login", "Sign Up"),
                index=0, # Default to Login
                key="auth_choice_radio",
                horizontal=True # Display radio buttons horizontally
            )
            st.markdown("---") # Separator

            if auth_choice == "Login":
                login_form_ui()
            else:
                signup_form_ui()
            
            st.markdown("</div>", unsafe_allow_html=True) # Close the styled div
    
    st.markdown("<br><br>", unsafe_allow_html=True) # More space at bottom
else:
    # --- Main Application Content (Visible only if logged in) ---
    st.sidebar.markdown(f"Welcome, **{st.session_state.username}**!", unsafe_allow_html=True)
    if st.sidebar.button("Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.prompt_history = []
        st.session_state.search_input = ""
        st.session_state.selected_drug_for_details = ""
        st.session_state.question_input_value = ""
        st.rerun()

    # --- Section 1: Quick Drug Search (Type & Click) ---
    st.header("1. Quick Drug Search (Type & Click)")
    st.markdown("Start typing a drug name. Click on a suggestion to see its full details from the inventory.")

    search_term = st.text_input("Search by Drug Name or Generic Name:", key="drug_search_input", value=st.session_state.search_input)

    def select_drug_and_display(drug_name):
        st.session_state.selected_drug_for_details = drug_name
        st.session_state.search_input = ""
        st.rerun()

    if search_term:
        suggestion_query = f"""
        SELECT DISTINCT DRUG_NAME FROM PHARMACY_INVENTORY WHERE DRUG_NAME LIKE '%{search_term}%'
        UNION
        SELECT DISTINCT GENERIC_NAME FROM PHARMACY_INVENTORY WHERE GENERIC_NAME LIKE '%{search_term}%' AND GENERIC_NAME IS NOT NULL
        LIMIT 10;
        """
        
        with st.spinner("Searching for suggestions..."):
            suggestions_raw, _ = execute_sql_query(suggestion_query)
            suggestions = [s[0] for s in suggestions_raw if s[0] is not None] if suggestions_raw else []

        if suggestions:
            st.subheader("Suggestions:")
            suggestion_cols = st.columns(3)
            for i, drug_name in enumerate(suggestions):
                with suggestion_cols[i % 3]:
                    if st.button(drug_name, key=f"suggest_btn_{drug_name}"):
                        select_drug_and_display(drug_name)
        else:
            st.info(f"No suggestions found for '{search_term}'.")
    else:
        st.info("Start typing in the search box to see drug suggestions.")

    if st.session_state.selected_drug_for_details:
        selected_drug_name = st.session_state.selected_drug_for_details
        st.subheader(f"Details for: {selected_drug_name}")
        details_query = f"""
        SELECT * FROM PHARMACY_INVENTORY 
        WHERE DRUG_NAME = '{selected_drug_name}' OR GENERIC_NAME = '{selected_drug_name}';
        """
        details_data, details_columns = execute_sql_query(details_query)
        
        if details_data:
            if details_columns:
                df_data = [dict(zip(details_columns, row)) for row in details_data]
                st.dataframe(df_data)
            else:
                st.write(details_data)
        else:
            st.info(f"Could not retrieve full details for {selected_drug_name}.")

    st.markdown("---")


    # --- Section 2: Add New Records (Side-by-Side) ---
    st.header("2. Add New Records")
    st.markdown("Use the forms below to add new drugs to inventory or new patient diagnostic data.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Add New Drug to Inventory")
        with st.form("add_drug_form"):
            drug_name = st.text_input("Drug Name (e.g., 'Aspirin')", key="form_drug_name")
            generic_name = st.text_input("Generic Name (Optional, e.g., 'Acetylsalicylic Acid')", key="form_generic_name")
            formulation = st.selectbox("Formulation", ['Tablet', 'Capsule', 'Syrup', 'Injection', 'Inhaler'], key="form_formulation")
            dosage = st.text_input("Dosage (e.g., '81mg', '5ml')", key="form_dosage")
            pack_size = st.text_input("Pack Size (e.g., '30 tabs', '100ml')", key="form_pack_size")
            price_per_pack = st.number_input("Price Per Pack", min_value=0.01, format="%.2f", key="form_price_per_pack")
            stock_quantity = st.number_input("Stock Quantity", min_value=0, step=1, key="form_stock_quantity")
            expiry_date = st.date_input("Expiry Date", min_value=date.today(), key="form_expiry_date")
            supplier = st.text_input("Supplier (e.g., 'PharmaCorp')", key="form_supplier")

            submitted = st.form_submit_button("Add Drug")

            if submitted:
                if not drug_name:
                    st.error("Drug Name is required.")
                else:
                    insert_query = f"""
                    INSERT INTO PHARMACY_INVENTORY (DRUG_NAME, GENERIC_NAME, FORMULATION, DOSAGE, PACK_SIZE, PRICE_PER_PACK, STOCK_QUANTITY, EXPIRY_DATE, SUPPLIER)
                    VALUES ('{drug_name}', {'NULL' if not generic_name else f"'{generic_name}'"}, '{formulation}', '{dosage}', '{pack_size}', {price_per_pack}, {stock_quantity}, '{expiry_date.strftime('%Y-%m-%d')}', '{supplier}');
                    """
                    status_msg, _ = execute_sql_query(insert_query)
                    if status_msg:
                        st.success(f"Drug '{drug_name}' added successfully! You can now query it using natural language.")
                    else:
                        st.error("Failed to add drug. Please check details and try again.")


    with col2:
        st.subheader("Add New Diagnostic Record")
        available_drugs_query = "SELECT DRUG_ID, DRUG_NAME FROM PHARMACY_INVENTORY ORDER BY DRUG_NAME ASC;"
        drug_options_raw, _ = execute_sql_query(available_drugs_query)
        drug_options = {row[1]: row[0] for row in drug_options_raw} if drug_options_raw else {}
        drug_names_for_select = ["(None - No Drug Prescribed)"] + sorted(drug_options.keys())

        with st.form("add_diagnostic_form"):
            patient_name = st.text_input("Patient Name", key="form_patient_name_diag")
            diagnosis = st.text_input("Diagnosis (e.g., 'Hypertension')", key="form_diagnosis")
            diagnosis_date = st.date_input("Diagnosis Date", max_value=date.today(), key="form_diagnosis_date")
            test_results = st.text_area("Test Results Summary", key="form_test_results")
            
            selected_drug_name_for_prescribed = st.selectbox(
                "Drug Prescribed (Optional)",
                options=drug_names_for_select,
                key="form_drug_prescribed_select"
            )
            drug_id_prescribed = drug_options.get(selected_drug_name_for_prescribed) if selected_drug_name_for_prescribed != "(None - No Drug Prescribed)" else 'NULL'


            submitted_diag = st.form_submit_button("Add Record")

            if submitted_diag:
                if not patient_name or not diagnosis:
                    st.error("Patient Name and Diagnosis are required.")
                else:
                    insert_query_diag = f"""
                    INSERT INTO DIAGNOSTIC_DATA (PATIENT_NAME, DIAGNOSIS, DIAGNOSIS_DATE, TEST_RESULTS, DRUG_ID_PRESCRIBED)
                    VALUES ('{patient_name}', '{diagnosis}', '{diagnosis_date.strftime('%Y-%m-%d')}', '{test_results}', {drug_id_prescribed});
                    """
                    status_msg_diag, _ = execute_sql_query(insert_query_diag)
                    if status_msg_diag:
                        st.success(f"Diagnostic record for '{patient_name}' added successfully!")
                    else:
                        st.error("Failed to add diagnostic record. Please check details and try again.")
    st.markdown("---")


    # --- Section 3: Delete Record by ID ---
    st.header("3. Delete Record by ID")
    st.markdown("You can delete records from `PHARMACY_INVENTORY` or `DIAGNOSTIC_DATA` by specifying the ID.")

    delete_table = st.selectbox("Select Table to Delete From:", ['PHARMACY_INVENTORY', 'DIAGNOSTIC_DATA'], key="delete_table_select")
    delete_id = st.number_input(f"Enter the {delete_table} ID to delete:", min_value=1, step=1, key="delete_id_input")

    if st.button(f"Delete Record from {delete_table}", key="delete_record_btn"):
        if delete_id:
            st.info(f"Attempting to delete record with ID {delete_id} from {delete_table}...")
            
            delete_query = f"DELETE FROM {delete_table} WHERE {'DRUG_ID' if delete_table == 'PHARMACY_INVENTORY' else 'PATIENT_ID'} = {delete_id};"
            status_msg, _ = execute_sql_query(delete_query)
            if status_msg:
                st.success(f"Record with ID {delete_id} from {delete_table} deleted successfully! Please re-query to verify.")
            else:
                st.error("Failed to delete record. It might not exist or a database error occurred.")
        else:
            st.error("Please enter an ID to delete.")

    st.markdown("---")


    # --- Section 4: Natural Language Query (Advanced) ---
    st.header("4. Natural Language Query (Advanced)")
    st.markdown("Type natural language questions or commands for more complex queries across **Pharmacy Inventory** and **Diagnostic Data**.")

    user_typed_question = st.text_input(
        "Enter your query or command:",
        value=st.session_state.question_input_value,
        key="main_input_text"
    )

    st.subheader("Or choose from a suggestion:")

    suggested_prompts = [
        "Show all drugs with less than 50 packs in stock.",
        "List all drugs supplied by PharmaCorp.",
        "Which drugs are expiring before 2026-12-31?",
        "List patient names with a 'Diabetes Type 2' diagnosis.",
        "What drugs were prescribed for patients diagnosed with 'Asthma'?",
        "Show the diagnosis and prescribed drug for patient Amit Sharma.",
        "How many diagnoses were made in 2024?",
        "Sell 5 packs of Ibuprofen 200mg tablets.",
        "Restock 15 packs of Metformin 500mg tablets.",
        "What is the stock quantity for Lipitor 20mg tablets?",
        "Add a new drug: Ibuprofen, Ibuprofen, Tablet, 400mg, 50 tabs, 4.00 price, 200 stock, 2027-01-01 expiry, supplied by GenericMeds.",
        "Delete drug with DRUG_ID 1."
    ]

    def set_question_and_submit_llm(prompt_text):
        st.session_state.question_input_value = prompt_text
        st.session_state.trigger_submit_llm = True
        st.rerun()

    cols_llm_suggestions = st.columns(3)

    for i, prompt_text in enumerate(suggested_prompts):
        with cols_llm_suggestions[i % 3]:
            if st.button(prompt_text, key=f"suggest_llm_{i}"):
                set_question_and_submit_llm(prompt_text)

    submit_button_clicked_llm = st.button("Generate SQL Query & Execute", key="manual_submit_llm")

    if st.session_state.get('trigger_submit_llm', False):
        submit_button_clicked_llm = True
        st.session_state.trigger_submit_llm = False

    if submit_button_clicked_llm:
        current_question_llm = st.session_state.question_input_value if st.session_state.question_input_value else user_typed_question
        
        if current_question_llm.strip() == "":
            st.warning("Please enter a query or command, or choose a suggestion.")
        else:
            with st.spinner("Generating SQL query..."):
                generated_sql_query = get_gemini_response(current_question_llm, LLM_PROMPT)

            if generated_sql_query and not generated_sql_query.startswith("Error:"):
                st.subheader("Generated SQL Query:")
                st.code(generated_sql_query, language="sql")

                st.subheader("Query Results/Status:")
                
                query_results_data, query_results_columns = execute_sql_query(generated_sql_query) 

                history_entry = {
                    "prompt": current_question_llm,
                    "sql": generated_sql_query,
                    "result": query_results_data if isinstance(query_results_data, str) else "Data Retrieved",
                    "status": "Success"
                }
                if query_results_data is not None and isinstance(query_results_data, list) and not query_results_data:
                    history_entry["result"] = "No results found"
                st.session_state.prompt_history.append(history_entry)

                if query_results_data is not None:
                    if isinstance(query_results_data, str): 
                        st.success(query_results_data)
                        if generated_sql_query.strip().upper().startswith(("UPDATE", "INSERT", "DELETE")):
                            st.info("The database has been modified. You can run a SELECT query to see the changes.")
                    else:
                        if query_results_data:
                            try:
                                if query_results_columns:
                                    df_data_llm = [dict(zip(query_results_columns, row)) for row in query_results_data]
                                    st.dataframe(df_data_llm)
                                else:
                                    st.write(query_results_data)
                            except Exception as e:
                                st.write(query_results_data)
                                st.warning(f"Could not display results as a table/dataframe: {e}")
                        else:
                            st.info("No results found for your query. Check the query and database content, or criteria.")
                else:
                    history_entry["status"] = "Error"
                    history_entry["result"] = "Database error occurred (see above)."
            elif generated_sql_query.startswith("Error:"):
                history_entry = {
                    "prompt": current_question_llm,
                    "sql": "N/A",
                    "result": generated_sql_query,
                    "status": "AI Generation Error"
                }
                st.session_state.prompt_history.append(history_entry)
                pass

    st.markdown("---")

    # --- Show Prompt History Button ---
    if st.button("Show Prompt History", key="show_history_btn"):
        if st.session_state.prompt_history:
            st.subheader("Query History:")
            for i, entry in enumerate(reversed(st.session_state.prompt_history)):
                with st.expander(f"Prompt {len(st.session_state.prompt_history) - i}: {entry['prompt'][:50]}..."):
                    st.markdown(f"**Prompt:** {entry['prompt']}")
                    st.markdown(f"**Generated SQL:**")
                    st.code(entry['sql'], language="sql")
                    st.markdown(f"**Result/Status:** {entry['result']}")
                    st.markdown(f"**Overall Status:** `{entry['status']}`")
                    st.markdown("---")
        else:
            st.info("No prompt history yet. Type a query or command and execute it!")
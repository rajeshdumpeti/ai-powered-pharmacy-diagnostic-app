# app.py
import streamlit as st
from datetime import date # Added for forms

# Import functions from your modules
from database_ops import init_db, execute_sql_query, DATABASE_FILE
from gemini_client import get_gemini_response
from prompts import LLM_PROMPT

# Call init_db at the beginning of the script to ensure tables and data exist
init_db()


# --- Streamlit APP ---
st.set_page_config(page_title="Rajesh's | Pharmacy & Diagnostics SQL Assistant", page_icon="⚕️", layout="wide")

st.markdown("## Rajesh's Gemini App - Your AI-Powered **Pharmacy & Diagnostics SQL Assistant**")
st.markdown("#### Comprehensive tool for managing pharmacy inventory and patient diagnostic data.")


# Initialize session state for various components
if 'search_input' not in st.session_state:
    st.session_state.search_input = ""
if 'selected_drug_for_details' not in st.session_state:
    st.session_state.selected_drug_for_details = ""
if 'question_input_value' not in st.session_state:
    st.session_state.question_input_value = ""
if 'prompt_history' not in st.session_state:
    st.session_state.prompt_history = []


# --- Section 1: Quick Drug Search (Type & Click) ---
st.header("1. Quick Drug Search (Type & Click)")
st.markdown("Start typing a drug name. Click on a suggestion to see its full details from the inventory.")

search_term = st.text_input("Search by Drug Name or Generic Name:", key="drug_search_input", value=st.session_state.search_input)

# Function to set the selected drug and trigger a rerun
def select_drug_and_display(drug_name):
    st.session_state.selected_drug_for_details = drug_name
    st.session_state.search_input = "" # Clear search input after selection
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

# Display details for the selected drug (if any)
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


# --- Section 2 & 3: Add New Drug Record & Add New Diagnostic Record (Side-by-Side) ---
st.header("2. Add New Records")
st.markdown("Use the forms below to add new drugs to inventory or new patient diagnostic data.")

col1, col2 = st.columns(2) # Create two columns for side-by-side display

# --- Column 1: Add New Drug Record ---
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


# --- Column 2: Add New Diagnostic Record ---
with col2:
    st.subheader("Add New Diagnostic Record")
    # Get available drug names for selection (for DRUG_ID_PRESCRIBED)
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
        # Convert selected drug name back to DRUG_ID
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
st.header("3. Delete Record by ID") # Updated header number
st.markdown("You can delete records from `PHARMACY_INVENTORY` or `DIAGNOSTIC_DATA` by specifying the ID.")

delete_table = st.selectbox("Select Table to Delete From:", ['PHARMACY_INVENTORY', 'DIAGNOSTIC_DATA'], key="delete_table_select")
delete_id = st.number_input(f"Enter the {delete_table} ID to delete:", min_value=1, step=1, key="delete_id_input")

if st.button(f"Delete Record from {delete_table}", key="delete_record_btn"):
    if delete_id:
        confirm_delete = st.warning(f"Are you sure you want to delete record with ID {delete_id} from {delete_table}? This action cannot be undone.")
        
        # Simple confirmation mechanism without a second button for brevity.
        # In a real app, you'd want a separate confirmation step (e.g., a modal with Yes/No buttons).
        delete_query = f"DELETE FROM {delete_table} WHERE {'DRUG_ID' if delete_table == 'PHARMACY_INVENTORY' else 'PATIENT_ID'} = {delete_id};"
        status_msg, _ = execute_sql_query(delete_query)
        if status_msg:
            st.success(f"Record with ID {delete_id} from {delete_table} deleted successfully!")
        else:
            st.error("Failed to delete record. It might not exist or a database error occurred.")
    else:
        st.error("Please enter an ID to delete.")

st.markdown("---")


# --- Section 4: Natural Language Query (Advanced) ---
st.header("4. Natural Language Query (Advanced)") # Updated header number
st.markdown("Type natural language questions or commands for more complex queries across **Pharmacy Inventory** and **Diagnostic Data**. You can also use NLP for updates, inserts, and deletes now!")

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
                    # For updates/deletes, provide a hint to verify
                    if generated_sql_query.strip().upper().startswith(("UPDATE", "INSERT", "DELETE")):
                        st.info("The database has been modified. You can run a SELECT query (e.g., 'Show all drugs') to see the changes.")
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
from dotenv import load_dotenv
import streamlit as st
import os
import sqlite3
import google.generativeai as genai
import time
import re

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    st.error("Error: GOOGLE_API_KEY not found in environment variables. Please check your .env file.")
    st.stop()

# Function to load model and provide sql query as a response
def get_gemini_response(question, prompt, max_retries=3, initial_delay=5):
    model = genai.GenerativeModel('models/gemini-2.0-flash') # Using flash model as per your code
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt[0], question])
            cleaned_response = response.text.strip()
            cleaned_response = re.sub(r'```(?:\w+)?\s*(.*?)\s*```', r'\1', cleaned_response, flags=re.DOTALL)
            cleaned_response = cleaned_response.strip()
            return cleaned_response
        except genai.types.BlockedPromptException as e:
            st.error(f"The request was blocked: {e.safety_ratings}. Please refine your query.")
            return "Error: Query blocked due to safety concerns."
        except Exception as e:
            if "ResourceExhausted" in str(e):
                st.warning(f"API quota exceeded (attempt {attempt + 1}/{max_retries}). Please wait a moment.")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    st.error("Max retries reached for API call. Please try again later or check your Google API quotas.")
                    return "Error: API quota exceeded."
            else:
                st.error(f"An unexpected API error occurred: {e}")
                return "Error: An API error occurred."
    return "Error: Failed to get response after multiple retries."

# Function to read/execute SQL query from the database
def execute_sql_query(sql_query, db_path):
    conn = None
    rows = []
    columns = []
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql_query)
        
        if sql_query.strip().upper().startswith("SELECT"):
            columns = [description[0] for description in cur.description] if cur.description else []
            rows = cur.fetchall()
            return rows, columns
        else:
            conn.commit()
            return "Operation successful: Database updated.", None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        st.code(sql_query, language="sql")
        return None, None
    finally:
        if conn:
            conn.close()

# Define your prompt with both table schemas and examples
prompt = [
    """
You are an expert AI assistant specializing in converting natural language commands and questions into SQL queries.

The SQL database contains two tables:

**1. `PHARMACY_INVENTORY` (for drug information and stock)**
- `DRUG_ID` (INTEGER): Unique identifier for the drug (Primary Key). Auto-incremented.
- `DRUG_NAME` (VARCHAR): Brand name of the drug (e.g., 'Lipitor', 'Advil').
- `GENERIC_NAME` (VARCHAR): Generic name of the drug (e.g., 'Atorvastatin', 'Ibuprofen'). Can be NULL.
- `FORMULATION` (VARCHAR): Form of the drug (e.g., 'Tablet', 'Capsule', 'Syrup', 'Injection', 'Inhaler').
- `DOSAGE` (VARCHAR): Dosage of the drug (e.g., '20mg', '500mg', '90mcg/puff', '5ml').
- `PACK_SIZE` (VARCHAR): Size of the package (e.g., '30 tabs', '100ml', '1 vial', '50 cap').
- `PRICE_PER_PACK` (REAL): Price of one pack of the drug (e.g., 12.50, 35.75).
- `STOCK_QUANTITY` (INT): Number of packs currently in stock (e.g., 150, 80).
- `EXPIRY_DATE` (DATE): Expiry date of the drug in 'YYYY-MM-DD' format.
- `SUPPLIER` (VARCHAR): Name of the drug supplier (e.g., 'PharmaCorp', 'MediSupply').

**2. `DIAGNOSTIC_DATA` (for patient diagnoses and prescribed drugs)**
- `PATIENT_ID` (INTEGER): Unique identifier for the patient (Primary Key). Auto-incremented.
- `PATIENT_NAME` (VARCHAR): Full name of the patient.
- `DIAGNOSIS` (VARCHAR): Medical diagnosis (e.g., 'Hypertension', 'Diabetes', 'Asthma').
- `DIAGNOSIS_DATE` (DATE): Date of diagnosis in 'YYYY-MM-DD' format.
- `TEST_RESULTS` (VARCHAR): Summary of test results.
- `DRUG_ID_PRESCRIBED` (INTEGER): Foreign key linking to `PHARMACY_INVENTORY.DRUG_ID`. Can be NULL if no drug was prescribed.

**Important Guidelines:**
1.  **Output should contain ONLY the SQL query.** No explanations, formatting markdown, or other text.
2.  Use proper SQL syntax.
3.  **Use `JOIN` clauses (specifically `INNER JOIN` or `LEFT JOIN`) when information is needed from both tables.**
    * `PHARMACY_INVENTORY.DRUG_ID` can be joined with `DIAGNOSTIC_DATA.DRUG_ID_PRESCRIBED`.
4.  For **read operations (questions)**, generate `SELECT` queries.
5.  For **update/sell/restock operations (commands)**, generate `UPDATE` queries on `PHARMACY_INVENTORY`.
6.  For date comparisons, use the format 'YYYY-MM-DD'.
7.  Use `LIKE` for partial string matches (e.g., `WHERE DRUG_NAME LIKE '%cillin%'`).
8.  Handle cases where a column might be NULL (e.g., `WHERE GENERIC_NAME IS NULL` or `WHERE DRUG_ID_PRESCRIBED IS NULL`).

Here are some examples of natural language questions and commands and their corresponding SQL queries:

**Pharmacy Inventory Examples (Single Table):**
- **Question**: "How many different tablet formulations do we have?"
- **SQL Query**: `SELECT COUNT(DISTINCT DRUG_NAME) FROM PHARMACY_INVENTORY WHERE FORMULATION = 'Tablet';`

- **Question**: "What is the stock quantity for Ibuprofen 200mg tablets?"
- **SQL Query**: `SELECT STOCK_QUANTITY FROM PHARMACY_INVENTORY WHERE DRUG_NAME = 'Ibuprofen' AND DOSAGE = '200mg' AND FORMULATION = 'Tablet';`

- **Command**: "I sold 5 packs of Atorvastatin 20mg tablets."
- **SQL Query**: `UPDATE PHARMACY_INVENTORY SET STOCK_QUANTITY = STOCK_QUANTITY - 5 WHERE DRUG_NAME = 'Atorvastatin' AND DOSAGE = '20mg' AND FORMULATION = 'Tablet';`

- **Command**: "Restock 10 packs of Metformin 500mg tablets."
- **SQL Query**: `UPDATE PHARMACY_INVENTORY SET STOCK_QUANTITY = STOCK_QUANTITY + 10 WHERE DRUG_NAME = 'Metformin' AND DOSAGE = '500mg' AND FORMULATION = 'Tablet';`

**Diagnostic Data Examples (Single Table):**
- **Question**: "List all patient names with a 'Hypertension' diagnosis."
- **SQL Query**: `SELECT PATIENT_NAME FROM DIAGNOSTIC_DATA WHERE DIAGNOSIS = 'Hypertension';`

- **Question**: "How many diagnoses were made in 2024?"
- **SQL Query**: `SELECT COUNT(*) FROM DIAGNOSTIC_DATA WHERE DIAGNOSIS_DATE BETWEEN '2024-01-01' AND '2024-12-31';`

- **Question**: "Show diagnostic data for patient Bob Johnson."
- **SQL Query**: `SELECT * FROM DIAGNOSTIC_DATA WHERE PATIENT_NAME = 'Bob Johnson';`

**Combined Pharmacy and Diagnostic Data Examples (Using JOINs):**
- **Question**: "List the names of patients who were prescribed 'Atorvastatin'."
- **SQL Query**: `SELECT D.PATIENT_NAME FROM DIAGNOSTIC_DATA AS D INNER JOIN PHARMACY_INVENTORY AS P ON D.DRUG_ID_PRESCRIBED = P.DRUG_ID WHERE P.DRUG_NAME = 'Atorvastatin';`

- **Question**: "What drugs were prescribed for patients diagnosed with 'Diabetes'?"
- **SQL Query**: `SELECT DISTINCT P.DRUG_NAME, P.GENERIC_NAME FROM PHARMACY_INVENTORY AS P INNER JOIN DIAGNOSTIC_DATA AS D ON P.DRUG_ID = D.DRUG_ID_PRESCRIBED WHERE D.DIAGNOSIS = 'Diabetes';`

- **Question**: "Show the diagnosis and prescribed drug for patient Alice Smith."
- **SQL Query**: `SELECT D.DIAGNOSIS, P.DRUG_NAME FROM DIAGNOSTIC_DATA AS D LEFT JOIN PHARMACY_INVENTORY AS P ON D.DRUG_ID_PRESCRIBED = P.DRUG_ID WHERE D.PATIENT_NAME = 'Alice Smith';`

- **Question**: "Find all patients who were prescribed any tablet formulation."
- **SQL Query**: `SELECT DISTINCT D.PATIENT_NAME FROM DIAGNOSTIC_DATA AS D INNER JOIN PHARMACY_INVENTORY AS P ON D.DRUG_ID_PRESCRIBED = P.DRUG_ID WHERE P.FORMULATION = 'Tablet';`

Now, generate an SQL query for the given question or command:
"""
]

# --- Streamlit APP ---
st.set_page_config(page_title="Rajesh's | Pharmacy & Diagnostics SQL Assistant", page_icon="⚕️", layout="wide") # Updated Title & Icon

st.markdown("## Rajesh's Gemini App - Your AI-Powered **Pharmacy & Diagnostics SQL Assistant**") # Updated header
st.markdown("#### Ask questions or give commands to manage your pharmacy inventory and patient diagnostic data using natural language.")


# Initialize session state for various components
if 'search_input' not in st.session_state:
    st.session_state.search_input = ""
if 'selected_drug_for_details' not in st.session_state:
    st.session_state.selected_drug_for_details = ""
if 'question_input_value' not in st.session_state:
    st.session_state.question_input_value = ""

# --- Filter and Display Pharmacy Section (Type & Click) ---
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
        suggestions_raw, _ = execute_sql_query(suggestion_query, 'student.db')
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
    details_data, details_columns = execute_sql_query(details_query, 'student.db')
    
    if details_data:
        if details_columns:
            df_data = [dict(zip(details_columns, row)) for row in details_data]
            st.dataframe(df_data)
        else:
            st.write(details_data)
    else:
        st.info(f"Could not retrieve full details for {selected_drug_name}.")

st.markdown("---")

# --- Natural Language Query Section ---
st.header("2. Natural Language Query (Advanced)")
st.markdown("Type natural language questions or commands for more complex queries across **Pharmacy Inventory** and **Diagnostic Data**.")

# User input for the question
user_typed_question = st.text_input(
    "Enter your query or command:",
    value=st.session_state.question_input_value,
    key="main_input_text"
)

# --- Prompt Suggestions Section (for LLM queries) ---
st.subheader("Or choose from a suggestion:")

# Define your suggested prompts for the LLM, including cross-table queries
suggested_prompts = [
    "Show all drugs with less than 50 packs in stock.",
    "List all drugs supplied by PharmaCorp.",
    "Which drugs are expiring before 2026-12-31?",
    "List patient names with a 'Diabetes' diagnosis.", # New
    "What drugs were prescribed for patients diagnosed with 'Asthma'?", # New (JOIN)
    "Show the diagnosis and prescribed drug for patient Alice Smith.", # New (LEFT JOIN)
    "How many diagnoses were made in 2024?", # New
    "Sell 5 packs of Ibuprofen 200mg tablets.",
    "Restock 15 packs of Metformin 500mg tablets.",
]

# Function to handle button click and update session state
def set_question_and_submit_llm(prompt_text):
    st.session_state.question_input_value = prompt_text
    st.session_state.trigger_submit_llm = True # Use a specific flag for LLM submit
    st.rerun() # Rerun to trigger the submission logic

cols_llm_suggestions = st.columns(3) # Adjust number of columns as needed

for i, prompt_text in enumerate(suggested_prompts):
    with cols_llm_suggestions[i % 3]:
        if st.button(prompt_text, key=f"suggest_llm_{i}"):
            set_question_and_submit_llm(prompt_text)

# Submit button for manual entry or after suggestion click
submit_button_clicked_llm = st.button("Generate SQL Query & Execute", key="manual_submit_llm")

# Logic to trigger submission if a suggestion button was clicked (for LLM queries)
if st.session_state.get('trigger_submit_llm', False):
    submit_button_clicked_llm = True
    st.session_state.trigger_submit_llm = False # Reset the flag

# If LLM submit is clicked
if submit_button_clicked_llm:
    current_question_llm = user_typed_question # Use the actual value from the text input
    
    if current_question_llm.strip() == "":
        st.warning("Please enter a query or command, or choose a suggestion.")
    else:
        with st.spinner("Generating SQL query..."):
            print(f"Sending to Gemini: '{current_question_llm}' (repr: {repr(current_question_llm)})")
            generated_sql_query = get_gemini_response(current_question_llm, prompt)

        if generated_sql_query and not generated_sql_query.startswith("Error:"):
            st.subheader("Generated SQL Query:")
            st.code(generated_sql_query, language="sql")

            st.subheader("Query Results/Status:")
            print(f"Attempting to execute SQL: '{generated_sql_query}' (repr: {repr(generated_sql_query)})") 
            
            query_results_data, query_results_columns = execute_sql_query(generated_sql_query, 'student.db') 

            if query_results_data is not None:
                if isinstance(query_results_data, str): 
                    st.success(query_results_data)
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
                pass # Error message already displayed by execute_sql_query
        elif generated_sql_query.startswith("Error:"):
            pass # Error message already displayed by get_gemini_response
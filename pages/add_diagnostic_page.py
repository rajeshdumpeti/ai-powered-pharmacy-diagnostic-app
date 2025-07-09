# pages/add_diagnostic_page.py
import streamlit as st
from datetime import date
from services.database_service import execute_sql_query, get_all_drugs_for_select # Import from new path

def show_add_diagnostic_page():
    st.header("Add New Diagnostic Record")
    st.markdown("Use the form below to add a new patient diagnostic data record.")

    available_drugs_query_raw, _ = get_all_drugs_for_select()
    drug_options = {row[1]: row[0] for row in available_drugs_query_raw} if available_drugs_query_raw else {}
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
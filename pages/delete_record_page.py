# pages/delete_record_page.py
import streamlit as st
from services.database_service import execute_sql_query # Import from new path

def show_delete_record_page():
    st.header("Delete Record by ID")
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
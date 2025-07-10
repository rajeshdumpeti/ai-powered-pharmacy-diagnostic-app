import streamlit as st
from services.database_service import execute_sql_query, fetch_all_drug_names

def show_quick_drug_search_page():
    st.markdown("### 🔍 Quick Drug Search")

    # Auto-suggest dropdown
    drug_names = fetch_all_drug_names()
    selected_drug = st.selectbox("Type or select drug name", drug_names)

    if selected_drug:
        query = f"SELECT * FROM PHARMACY_INVENTORY WHERE DRUG_NAME = '{selected_drug}'"
        result, columns = execute_sql_query(query)
        if result:
            st.table([dict(zip(columns, row)) for row in result])
        else:
            st.warning("No drug found with that name.")

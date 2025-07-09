# pages/quick_drug_search_page.py
import streamlit as st
from services.database_service import execute_sql_query # Import from new path

def show_quick_drug_search_page():
    st.header("Quick Drug Search (Type & Click)")
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
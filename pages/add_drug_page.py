# pages/add_drug_page.py
import streamlit as st
from datetime import date
from services.database_service import execute_sql_query # Import from new path

def show_add_drug_page():
    st.header("Add New Drug to Inventory")
    st.markdown("Use the form below to add a new drug to the pharmacy inventory.")

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
    st.markdown("---")
# pages/inventory_insights_page.py
import streamlit as st
from datetime import date
import pandas as pd
from services.database_service import execute_sql_query # Import from new path
from services.gemini_service import get_llm_analysis_from_data # Import from new path
from prompts import LLM_INVENTORY_INSIGHTS_PROMPT # Import from new path

def show_inventory_insights_page():
    st.header("AI-Driven Inventory Insights")
    st.markdown("Get actionable recommendations for your pharmacy inventory based on stock levels and expiry dates.")

    if st.button("Generate Inventory Insights", key="generate_inventory_insights_btn"):
        with st.spinner("Analyzing inventory for insights..."):
            current_date_str = date.today().strftime('%Y-%m-%d')
            future_date_str = (date.today() + pd.DateOffset(months=6)).strftime('%Y-%m-%d')
            
            inventory_insights_query = f"""
            SELECT DRUG_NAME, STOCK_QUANTITY, EXPIRY_DATE, SUPPLIER
            FROM PHARMACY_INVENTORY
            WHERE STOCK_QUANTITY < 50 OR EXPIRY_DATE <= '{future_date_str}'
            ORDER BY EXPIRY_DATE ASC, STOCK_QUANTITY ASC;
            """
            inventory_data_raw, inventory_cols = execute_sql_query(inventory_insights_query)

            if inventory_data_raw:
                inventory_data_df = [dict(zip(inventory_cols, row)) for row in inventory_data_raw]
                
                llm_insights = get_llm_analysis_from_data(
                    inventory_data_df,
                    LLM_INVENTORY_INSIGHTS_PROMPT,
                    original_request="Analyze pharmacy inventory for urgent attention items"
                )
                if llm_insights and not llm_insights.startswith("Error:"):
                    st.subheader("Pharmacy Inventory Insights & Recommendations:")
                    st.write(llm_insights)
                else:
                    st.error(llm_insights)
            else:
                st.info("No low stock or expiring drugs found. Inventory appears healthy!")
    st.markdown("---")
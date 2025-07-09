# pages/custom_report_page.py
import streamlit as st
from services.database_service import execute_sql_query # Import from new path
from services.gemini_service import generate_sql_query_from_prompt, get_llm_analysis_from_data # Import from new path
from prompts import LLM_SQL_GENERATION_PROMPT, LLM_REPORT_GENERATION_PROMPT # Import from new path

def show_custom_report_page():
    st.header("Custom Data Report Generation")
    st.markdown("Describe the report you need, and the AI will generate the SQL, fetch data, and summarize it into a human-readable report.")

    report_request = st.text_area(
        "Describe the report you want to generate (e.g., 'Monthly sales by drug type for 2023', 'Number of patients per diagnosis this year'):",
        key="report_request_input"
    )

    if st.button("Generate Custom Report", key="generate_custom_report_btn"):
        if report_request.strip():
            with st.spinner("Generating SQL and report..."):
                sql_query_for_report = generate_sql_query_from_prompt(report_request, LLM_SQL_GENERATION_PROMPT)

                if sql_query_for_report and not sql_query_for_report.startswith("Error:"):
                    st.subheader("Generated SQL Query for Report:")
                    st.code(sql_query_for_report, language="sql")

                    report_data_raw, report_cols = execute_sql_query(sql_query_for_report)

                    if report_data_raw:
                        report_data_df = [dict(zip(report_cols, row)) for row in report_data_raw]
                        
                        llm_report = get_llm_analysis_from_data(
                            report_data_df,
                            LLM_REPORT_GENERATION_PROMPT,
                            original_request=report_request
                        )
                        if llm_report and not llm_report.startswith("Error:"):
                            st.subheader("AI-Generated Custom Report:")
                            st.write(llm_report)
                        else:
                            st.error(llm_report)
                    else:
                        st.info("No data found for the specified report criteria. The generated SQL might need adjustment or the database is empty for this query.")
                else:
                    st.error(sql_query_for_report)
        else:
            st.warning("Please describe the report you want to generate.")
    st.markdown("---")
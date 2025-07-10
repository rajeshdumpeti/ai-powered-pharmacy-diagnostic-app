# pages/patient_summary_page.py
import streamlit as st
from services.database_service import execute_sql_query # Import from new path
from services.gemini_service import get_llm_analysis_from_data # Import from new path
from prompts import LLM_PATIENT_SUMMARY_PROMPT # Import from new path

def show_patient_summary_page():
    st.header("AI-Powered Patient History Summarizer")
    st.markdown("Get a concise, AI-generated summary of a patient's diagnostic and medication history.")

    patient_id_summary = st.number_input("Enter Patient ID for Summary:", min_value=1, step=1, key="patient_id_summary")
    if st.button("Generate Patient Summary", key="generate_patient_summary_btn"):
        if patient_id_summary:
            with st.spinner(f"Generating summary for Patient ID {patient_id_summary}..."):
                summary_query = f"""
                SELECT
                    DD.PATIENT_NAME,
                    DD.DIAGNOSIS,
                    DD.DIAGNOSIS_DATE,
                    DD.TEST_RESULTS,
                    PI.DRUG_NAME,
                    PI.DOSAGE
                FROM DIAGNOSTIC_DATA AS DD
                LEFT JOIN PHARMACY_INVENTORY AS PI ON DD.DRUG_ID_PRESCRIBED = PI.DRUG_ID
                WHERE DD.PATIENT_ID = {patient_id_summary}
                ORDER BY DD.DIAGNOSIS_DATE ASC;
                """
                summary_data_raw, summary_cols = execute_sql_query(summary_query)

                if summary_data_raw:
                    summary_data_df = [dict(zip(summary_cols, row)) for row in summary_data_raw]
                    
                    llm_summary = get_llm_analysis_from_data(
                        summary_data_df,
                        LLM_PATIENT_SUMMARY_PROMPT,
                        original_request=f"Summarize the health history for Patient ID {patient_id_summary}"
                    )
                    if llm_summary and not llm_summary.startswith("Error:"):
                        st.subheader(f"Summary for Patient ID {patient_id_summary}:")
                        st.write(llm_summary)
                    else:
                        st.error(llm_summary)
                else:
                    st.info(f"No diagnostic data found for Patient ID {patient_id_summary}.")
        else:
            st.warning("Please enter a Patient ID.")
    st.markdown("---")